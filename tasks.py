
from models import db, Transcription, SocialMediaContent



def create_audio_record(name, yt_url, audio_url, user):
    from app import app
    record = Transcription(
        name=name,
        yt_url=yt_url,
        audio_url=audio_url,
        user_id=user.id,
    )
    with app.app_context():
        db.session.add(record)
        db.session.flush()
        record_id = record.id
        db.session.commit()

    return record_id


def update_transcript_record(record_id, transcript_url, user_id):
    from app import app
    with app.app_context():
        record = Transcription.query.filter_by(id=record_id, user_id=user_id).first()
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
    
def update_notes_record(record_id, notes_url, model):
    from app import app
    with app.app_context():
        record = Transcription.query.get(record_id)
        if record is not None:
            if model == 'gpt-3.5-turbo':
                record.notes_url_gpt3 = notes_url
            elif model == 'gpt-4':
                record.notes_url_gpt4 = notes_url
            db.session.commit()

def get_transcription_record(record_id):
    from app import app
    with app.app_context():
        record = Transcription.query.get(record_id)
    return record

def update_social_media_content_record(record_id, model, content_type, content):
    from app import app
    with app.app_context():
        # Access the Transcription record
        record = Transcription.query.get(record_id)
        if record is not None:
            # Update the corresponding social media content
            social_media_content = SocialMediaContent.query.filter_by(transcription_id=record_id).first()
            if social_media_content is None:
                social_media_content = SocialMediaContent(transcription_id=record.id)
                db.session.add(social_media_content)
            
            # Remove '.' and '-' from the model name
            model_name = model.replace(".", "").replace("-", "").replace("turbo", "")
            content_type = content_type.replace("_single", "")
            print(f'{content_type}_{model_name}')
            setattr(social_media_content, f'{content_type}_{model_name}', content)
            db.session.commit()

