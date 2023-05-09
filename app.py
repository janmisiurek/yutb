from flask import Flask, render_template, request, abort, redirect, url_for
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

    if username == correct_username and password == correct_password:
        return True
    return False

@app.route('/', methods=['GET', 'POST'])
@auth.login_required
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        if not url:
            return abort(400, 'No URL provided')

        try:
            output_file = download_audio(url)
            filename = os.path.basename(output_file)  # Dodaj tę linię, aby pobrać tylko nazwę pliku
        except Exception as e:
            return abort(400, f"Error downloading audio: {str(e)}")

        return redirect(url_for('result', filename=filename))  # Zaktualizuj tę linię, aby używać zmiennej 'filename' zamiast 'output_file'

    return render_template('index.html')

@app.route('/result/<filename>')
@auth.login_required
def result(filename):
    return render_template('result.html', filename=filename)

if __name__ == '__main__':
    app.run(debug=True)