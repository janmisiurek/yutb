from flask import Flask, render_template, request, abort, redirect, url_for, send_from_directory
from flask_httpauth import HTTPBasicAuth
from dotenv import load_dotenv
import os
from youtube_utils import download_audio
from openai_utils import transcript
from rq import Queue
from worker import conn
from rq.job import Job

load_dotenv()

q = Queue(connection=conn)

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
        return redirect(url_for('result', filename=filename))
    else:
        return "Nay, job hasn't finished", 202

@app.route('/result/<filename>')
@auth.login_required
def result(filename):
    file_storage_path = os.path.join(app.root_path, 'download')
    file_path = os.path.join(file_storage_path, filename)
    if not os.path.exists(file_path):
        return abort(404, 'File not found')

    try:
        job = q.enqueue(transcript, file_path, app.root_path)
        while not job.is_finished:
            pass
        transcript_text, transcript_file_path = job.result
    except Exception as e:
        return abort(500, f"Error transcribing audio: {str(e)}")

    transcript_filename = os.path.basename(transcript_file_path)

    return render_template('result.html', filename=filename, transcript=transcript_text, transcript_filename=transcript_filename)

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
