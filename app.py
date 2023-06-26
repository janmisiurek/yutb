from flask import Flask, render_template, request, abort, redirect, url_for, send_from_directory, flash
from flask_httpauth import HTTPBasicAuth
from dotenv import load_dotenv
import os
from jobs import download_transcribe_generate_notes
from aws_utils import *
from rq import Queue
from worker import conn
from rq.job import Job
from models import db, Transcription, SocialMediaContent, User
import tempfile
from openai_utils import generate_social_media_content
import logging
from authlib.integrations.flask_client import OAuth
from flask_login import LoginManager, login_required, login_user, logout_user, current_user


load_dotenv()
BUCKET_NAME = os.getenv('BUCKET_NAME')
LINKEDIN_CLIENT_ID = os.getenv('LINKEDIN_CLIENT_ID')
LINKEDIN_CLIENT_SECRET = os.getenv('LINKEDIN_CLIENT_SECRET')
LINKEDIN_REDIRECT_URI = os.getenv('LINKEDIN_REDIRECT_URI')

q = Queue(connection=conn)

app = Flask(__name__)
auth = HTTPBasicAuth()
oauth = OAuth(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:////tmp/test.db')
app.secret_key = os.environ.get('FLASK_SECRET_KEY')
login_manager = LoginManager()
login_manager.init_app(app)

db.init_app(app)

linkedin = oauth.register(
    name='linkedin',
    client_id=LINKEDIN_CLIENT_ID,
    client_secret=LINKEDIN_CLIENT_SECRET,
    access_token_url='https://www.linkedin.com/oauth/v2/accessToken',
    access_token_params=None,
    authorize_url='https://www.linkedin.com/oauth/v2/authorization',
    authorize_params=None,
    api_base_url='https://api.linkedin.com/v2/',
    client_kwargs={
        'scope': 'r_liteprofile', 
        'redirect_uri': LINKEDIN_REDIRECT_URI,
        'token_endpoint_auth_method': 'client_secret_post',
    },
)


with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@auth.verify_password
def verify_password(username, password):
    correct_username = os.getenv("YUTB_USERNAME")
    correct_password = os.getenv("YUTB_PASSWORD")
    return (username == correct_username and password == correct_password)

@app.route('/home', methods=['GET'])
def home():
    return render_template('home.html')

@app.route('/login')
def login():
    redirect_uri = url_for('authorize', _external=True)
    return linkedin.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    token = linkedin.authorize_access_token()
    response = linkedin.get('me', token=token)
    profile = response.json()

    user = User.query.get(profile['id'])
    if user:
        login_user(user)
        return redirect(url_for('index'))

    user = User(
        id=profile['id'],
        first_name=profile['localizedFirstName'],
        last_name=profile['localizedLastName']
    )
    db.session.add(user)
    db.session.commit()
    login_user(user)

    return redirect(url_for('welcome', user_id=user.id))


@app.route('/welcome/<user_id>')
def welcome(user_id):
    user = User.query.get(user_id)
    if not user:
        return "User not found", 404

    return render_template("welcome.html", user=user)

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        tempo = request.form.get('tempo')
        content_types = request.form.getlist('content_types')

        if not url:
            return abort(400, 'No URL provided')

        if not tempo:
            return abort(400, 'No tempo provided')

        try:
            logging.info(f'Adding download_transcribe_create_notes job for url: {url}')
            job = q.enqueue(download_transcribe_generate_notes, url, tempo, content_types)
            logging.info(f'Added download_transcribe_create_notes job with id: {job.id}')
        except Exception as e:
            logging.error(f"Error downloading, transcribing, and creating notes: {str(e)}")
            return abort(400, f"Error downloading, transcribing, and creating notes: {str(e)}")

        flash("Transcription, note creation and social media content generation in progress")
        return redirect(url_for('dashboard2'))
    
    return render_template('index.html')


@app.route("/job/<job_id>", methods=['GET'])
@auth.login_required
def job_status(job_id):
    job = Job.fetch(job_id, connection=conn)

    if job.is_finished:
        transcript_text, transcript_file_path, yt_url = job.result
        transcript_filename = os.path.basename(transcript_file_path)
        return render_template('result.html', filename=transcript_filename, transcript=transcript_text, transcript_filename=transcript_filename)
    else:
        return "Job is still in progress"



@app.route('/download/<path:filename>')
@auth.login_required
def download_file(filename):
    
    presigned_url = create_presigned_url(BUCKET_NAME, filename)

    if presigned_url is None:
        abort(404, "File not found")

    return redirect(presigned_url)

@app.route('/dashboard')
@auth.login_required
def dashboard():
    files = list_files(BUCKET_NAME)

    audio_files = [file for file in files if file.startswith('download/')]
    transcription_files = [file for file in files if file.startswith('transcriptions/')]

    return render_template('dashboard.html', audio_files=audio_files, transcription_files=transcription_files)

@app.route('/dashboard2')
@auth.login_required
def dashboard2():
    with app.app_context():
        transcriptions = Transcription.query.all()
    return render_template('dashboard2.html', transcriptions=transcriptions)

@app.route('/notes/<record_id>', methods=['GET', 'POST'])
@auth.login_required
def notes(record_id):
    # Get the transcription record
    transcription = Transcription.query.get(record_id)
    if not transcription:
        abort(404, description="Record not found")

    # Download the notes from S3
    local_path_gpt4 = os.path.join(tempfile.gettempdir(), f"{record_id}_gpt4.txt")
    download_from_s3(BUCKET_NAME, transcription.notes_url_gpt4, local_path_gpt4)

    with open(local_path_gpt4, 'r') as file:
        notes_gpt4 = file.read().replace('\n', '<br>')

    # If the form was submitted, generate the selected types of social media content
    if request.method == 'POST':
        content_types = request.form.getlist('content_types')
        
        try:
            logging.info(f'Adding generate_social_media_content job for record_id: {record_id}')
            job = q.enqueue(generate_social_media_content, record_id, content_types)
            logging.info(f'Added generate_social_media_content job with id: {job.id}')
        except Exception as e:
            logging.error(f"Error generating social media content: {str(e)}")
            return abort(400, f"Error generating social media content: {str(e)}")

        flash("Social media content generation in progress")

    # Get the social media content record
    social_media_content = SocialMediaContent.query.filter_by(transcription_id=record_id).first()

    if social_media_content:
        fields = ['tweet_gpt35', 'tweet_gpt4', 'tweet_thread_gpt35', 'tweet_thread_gpt4', 'linkedin_post_gpt35', 'linkedin_post_gpt4']
        for field in fields:
            field_content = getattr(social_media_content, field)
            if field_content:
                setattr(social_media_content, field, field_content.replace('\n', '<br>'))

    os.remove(local_path_gpt4)

    return render_template('notes.html', 
                           name=transcription.name, 
                           notes_gpt4=notes_gpt4, 
                           social_media_content=social_media_content)

if __name__ == '__main__':
    app.run(debug=True)
