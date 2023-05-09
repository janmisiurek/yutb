from flask import Flask, render_template, request, abort
from flask_httpauth import HTTPBasicAuth
from dotenv import load_dotenv
import os

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
        # Tutaj będzie logika przetwarzania linku.
        pass

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)