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
        audio_url='download/' + name_without_extension + '.mp3', 
        transcript_url=transcript_file_path
    )

    with app.app_context():
        db.session.add(record)
        db.session.commit()
        
    return transcript_text, transcript_file_path, audio_file_path, yt_url