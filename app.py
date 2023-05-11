from flask import Flask, render_template, request, abort, redirect, url_for, send_from_directory
from flask_httpauth import HTTPBasicAuth
from dotenv import load_dotenv
import os
from youtube_utils import download_audio


load_dotenv()

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
            output_file = download_audio(url)
            filename = os.path.basename(output_file)
        except Exception as e:
            return abort(400, f"Error downloading audio: {str(e)}")

        return redirect(url_for('result', filename=filename))

    return render_template('index.html')

@app.route('/result/<filename>')
@auth.login_required
def result(filename):
    
    file_storage_path = os.path.join(app.root_path, 'download')

    file_path = os.path.join(file_storage_path, filename)
    if not os.path.exists(file_path):
        return abort(404, 'File not found')

    return render_template('result.html', filename=filename)


@app.route('/download/<filename>')
@auth.login_required
def download_file(filename):
    
    file_storage_path = os.path.join(app.root_path, 'download')
    try:
        return send_from_directory(file_storage_path, filename, as_attachment=True)
    except FileNotFoundError:
        abort(404, "File not found")

if __name__ == '__main__':
    app.run(debug=True)