from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Transcription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    yt_url = db.Column(db.String(256))
    audio_url = db.Column(db.String(256))
    transcript_url = db.Column(db.String(256))
    notes_url_gpt4 = db.Column(db.String(256))

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
