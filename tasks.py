
from models import db, Transcription



def create_audio_record(name, yt_url, audio_url):
    from app import app
    record = Transcription(
        name=name,
        yt_url=yt_url,
        audio_url=audio_url
    )
    with app.app_context():
        db.session.add(record)
        db.session.flush()
        record_id = record.id
        db.session.commit()

    return record_id


def update_transcript_record(record_id, transcript_url):
    from app import app
    with app.app_context():
        record = Transcription.query.get(record_id)
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
    
# Helper function combines the download and transcript functions for asynchronous execution as an RQ job, ensuring the transcript job is queued after the download job.