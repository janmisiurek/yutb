from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Transcription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    yt_url = db.Column(db.String(256))
    audio_url = db.Column(db.String(256))
    transcript_url = db.Column(db.String(256))
    notes_url_gpt3 = db.Column(db.String(256))
    notes_url_gpt4 = db.Column(db.String(256))
