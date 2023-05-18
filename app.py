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

load_dotenv()

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
            job = q.enqueue(download_audio, url)
        except Exception as e:
            return abort(400, f"Error downloading audio: {str(e)}")

        return redirect(url_for('job_status', job_id=job.get_id()))

    return render_template('index.html')

@app.route("/job/<job_id>", methods=['GET'])
@auth.login_required
def job_status(job_id):
    print(f"Checking status of job: {job_id}")
    job = Job.fetch(job_id, connection=conn)

    print(f"Job status: {job.get_status()}")
    if job.is_finished:
        filename, yt_url = job.result
        print(f"Job finished. Starting transcription job for file: {filename}")
        transcribe_job = q.enqueue(transcript, filename, yt_url, app.root_path)
        return redirect(url_for('transcribe_status', job_id=transcribe_job.get_id()))
    else:
        print("Job still in progress.")
        return render_template('job_status.html', job_status="Job is in progress: downloading audio")

@app.route("/transcribe/<job_id>", methods=['GET'])
@auth.login_required
def transcribe_status(job_id):
    job = Job.fetch(job_id, connection=conn)

    if job.is_finished:
        transcript_text, transcript_file_path, yt_url = job.result
        transcript_filename = os.path.basename(transcript_file_path)

        # Remove file extensions from the name
        name_without_extension = os.path.splitext(transcript_filename)[0]  # Remove .txt
        name_without_extension = os.path.splitext(name_without_extension)[0]  # Remove .mp4

        # Create new Transcription record
        record = Transcription(
            name=name_without_extension,
            yt_url=yt_url, 
            audio_url='download/' + name_without_extension + '.mp4', 
            transcript_url=transcript_file_path
        )
        db.session.add(record)
        db.session.commit()

        return render_template('result.html', filename=transcript_filename, transcript=transcript_text, transcript_filename=transcript_filename)
    else:
        return render_template('job_status.html', job_status="Job is in progress: transcribing audio")


@app.route('/download/<path:folder>/<path:filename>')
@auth.login_required
def download_file(folder, filename):
    # Generuj pre-signed URL do pliku
    file_path = os.path.join(folder, filename)
    presigned_url = create_presigned_url('wiadroborka', file_path)

    if presigned_url is None:
        abort(404, "File not found")

    # Przekieruj użytkownika do pre-signed URL
    return redirect(presigned_url)

@app.route('/dashboard')
@auth.login_required
def dashboard():
    # Pobierz listę plików z bucketu S3
    files = list_files('wiadroborka')

    # Rozdziel pliki na audio i transkrypcje na podstawie katalogu w nazwie pliku
    audio_files = [file for file in files if file.startswith('download/')]
    transcription_files = [file for file in files if file.startswith('transcriptions/')]

    return render_template('dashboard.html', audio_files=audio_files, transcription_files=transcription_files)

@app.route('/dashboard2')
@auth.login_required
def dashboard2():
    # Pobierz wszystkie rekordy transkrypcji z bazy danych
    with app.app_context():
        transcriptions = Transcription.query.all()
    return render_template('dashboard2.html', transcriptions=transcriptions)


if __name__ == '__main__':
    app.run(debug=True)
