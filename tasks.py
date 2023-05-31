from rq import Queue
from rq.decorators import job
from worker import conn
from models import db, Transcription

import os

q = Queue(connection=conn)

@job('default', connection=conn, timeout=3600)
def add_to_database(transcript_output):
    from app import app

    transcript_text, transcript_file_path, audio_file_path, yt_url = transcript_output
    name_without_extension = os.path.splitext(os.path.basename(transcript_file_path))[0]
    name_without_extension = os.path.splitext(name_without_extension)[0]

    record = Transcription(
        name=name_without_extension,
        yt_url=yt_url, 
        audio_url=name_without_extension + '.mp3', 
        transcript_url=transcript_file_path
    )

    with app.app_context():
        db.session.add(record)
        db.session.commit()
        
    return transcript_text, transcript_file_path, audio_file_path, yt_url


def create_audio_record(name, yt_url, audio_url):
    from app import app
    record = Transcription(
        name=name,
        yt_url=yt_url,
        audio_url=audio_url
    )
    with app.app_context():
        db.session.add(record)
        db.session.commit()

    return record


def update_transcript_record(yt_url, transcript_url):
    from app import app
    with app.app_context():
        record = Transcription.query.filter_by(yt_url=yt_url).first()
        if record is not None:
            record.transcript_url = transcript_url
            db.session.commit()


def get_audio_record(id):
    from app import app
    with app.app_context():
        record = Transcription.query.get(id)
    return record

def get_record_id(record):
    from app import app
    with app.app_context():
        return record.id