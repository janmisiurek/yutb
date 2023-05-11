from flask import Flask, render_template, request, abort, redirect, url_for, send_from_directory
from flask_httpauth import HTTPBasicAuth
from dotenv import load_dotenv
import os
from youtube_utils import download_audio
from openai_utils import transcript
from rq import Queue
from worker import conn
from rq.job import Job
import redis

load_dotenv()

q = Queue(connection=redis.from_url(os.getenv('REDIS_URL')))


app = Flask(__name__)
auth = HTTPBasicAuth()

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
    job = Job.fetch(job_id, connection=conn)

    if job.is_finished:
        filename = os.path.basename(job.result)
        transcribe_job = q.enqueue(transcript, job.result, app.root_path)
        return redirect(url_for('transcribe_status', job_id=transcribe_job.get_id()))
    else:
        return render_template('job_status.html', job_status="Job is in progress: downloading audio")

@app.route("/transcribe/<job_id>", methods=['GET'])
@auth.login_required
def transcribe_status(job_id):
    job = Job.fetch(job_id, connection=conn)

    if job.is_finished:
        transcript_text, transcript_file_path = job.result
        transcript_filename = os.path.basename(transcript_file_path)
        return render_template('result.html', filename=transcript_filename, transcript=transcript_text, transcript_filename=transcript_filename)
    else:
        return render_template('job_status.html', job_status="Job is in progress: transcribing audio")


@app.route('/download/<path:folder>/<path:filename>')
@auth.login_required
def download_file(folder, filename):
    file_storage_path = os.path.join(app.root_path, folder)
    try:
        return send_from_directory(file_storage_path, filename, as_attachment=True)
    except FileNotFoundError:
        abort(404, "File not found")

@app.route('/dashboard')
@auth.login_required
def dashboard():
    audio_folder = os.path.join(app.root_path, 'download')
    transcription_folder = os.path.join(app.root_path, 'transcriptions')
    
    audio_files = os.listdir(audio_folder)
    transcription_files = os.listdir(transcription_folder)

    return render_template('dashboard.html', audio_files=audio_files, transcription_files=transcription_files)

if __name__ == '__main__':
    app.run(debug=True)
