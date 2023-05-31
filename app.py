from flask import Flask, render_template, request, abort, redirect, url_for, send_from_directory
from flask_httpauth import HTTPBasicAuth
from dotenv import load_dotenv
import os
from youtube_utils import download_audio
from openai_utils import transcript
from aws_utils import *
from rq import Queue
from worker import conn
from rq.job import Job
from models import db, Transcription
from tasks import add_to_database
import logging
from rq import get_current_job
import time

load_dotenv()
BUCKET_NAME = os.getenv('BUCKET_NAME')

q = Queue(connection=conn)

app = Flask(__name__)
auth = HTTPBasicAuth()
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:////tmp/test.db')

db.init_app(app)

with app.app_context():
    db.create_all()

@auth.verify_password
def verify_password(username, password):
    correct_username = os.getenv("YUTB_USERNAME")
    correct_password = os.getenv("YUTB_PASSWORD")
    return (username == correct_username and password == correct_password)

@app.route('/', methods=['GET', 'POST'])
@auth.login_required
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        if not url:
            return abort(400, 'No URL provided')

        try:
            logging.info(f'Adding download_audio job for url: {url}')
            download_job = q.enqueue(download_audio, url)
            logging.info(f'Added download_audio job with id: {download_job.id}')
            while not download_job.is_finished:
                time.sleep(1) 
            
            download_audio_output = download_job.result  
            logging.info('Adding transcript job...')
            transcript_job = q.enqueue(transcript, download_audio_output)
            logging.info(f'Added transcript job with id: {transcript_job.id}')

            
        except Exception as e:
            logging.error(f"Error downloading audio: {str(e)}")
            return abort(400, f"Error downloading audio: {str(e)}")

        return redirect(url_for('job_status', job_id=transcript_job.get_id()))

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


if __name__ == '__main__':
    app.run(debug=True)
