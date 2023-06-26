from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Transcription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    yt_url = db.Column(db.String(256))
    audio_url = db.Column(db.String(256))
    transcript_url = db.Column(db.String(256))
    notes_url_gpt4 = db.Column(db.String(256))
    user_id = db.Column(db.String, db.ForeignKey('user.id'))

class SocialMediaContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transcription_id = db.Column(db.Integer, db.ForeignKey('transcription.id'))
    tweet_gpt35 = db.Column(db.Text)
    tweet_thread_gpt35 = db.Column(db.Text)
    linkedin_post_gpt35 = db.Column(db.Text)
    tweet_gpt4 = db.Column(db.Text)
    tweet_thread_gpt4 = db.Column(db.Text)
    linkedin_post_gpt4 = db.Column(db.Text)
    transcription = db.relationship('Transcription', backref=db.backref('social_media_contents', lazy=True))

class User(db.Model, UserMixin):
    id = db.Column(db.String, primary_key=True)
    first_name = db.Column(db.String(64), index=True)
    last_name = db.Column(db.String(64), index=True)
    tokens = db.Column(db.Integer, default=3)
    transcriptions = db.relationship('Transcription', backref='user', lazy='dynamic')