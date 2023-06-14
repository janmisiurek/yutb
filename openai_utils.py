import openai
import os
from dotenv import load_dotenv
from rq.decorators import job
from worker import conn
import boto3
from tasks import update_transcript_record, get_audio_record, update_notes_record, get_transcription_record
from aws_utils import download_from_s3
from models import Transcription, SocialMediaContent
import tempfile
from tasks import update_social_media_content_record

load_dotenv()
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
BUCKET_NAME = os.getenv('BUCKET_NAME')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


@job('default', connection=conn, timeout=3600)
def transcript(id):
    # Fetch the record from the database
    record = get_audio_record(id)

    # If the record does not exist or it has no audio_url, we cannot proceed
    if record is None or record.audio_url is None:
        raise Exception("No audio record found for ID: " + str(id))

    # Prepare local file path for the downloaded audio file
    local_audio_path = os.path.join('/tmp', os.path.basename(record.audio_url))
    print('dowloanding audio from s3')
    # Download the audio file from S3 to local
    download_from_s3(BUCKET_NAME, record.audio_url, local_audio_path)
    
    print('Transcribing')
    audio_file = open(local_audio_path, "rb")
    transcript_data = openai.Audio.transcribe("whisper-1", audio_file, OPENAI_API_KEY)
    text = transcript_data['text']
    print(text)
    transcription_file_path = 'transcriptions/' + os.path.basename(local_audio_path) + '.txt'
    print('sending to s3')
    s3 = boto3.resource('s3', aws_access_key_id=S3_ACCESS_KEY, aws_secret_access_key=S3_SECRET_KEY)
    s3.Object(BUCKET_NAME, transcription_file_path).put(Body=text)

    # Update the database record
    print('updating record')
    update_transcript_record(record.id, transcription_file_path)
    print('updated')
    return text

@job('default', connection=conn, timeout=3600)
def generate_notes(record_id):
    # Fetch the record from the database
    record = get_transcription_record(record_id)

    # If the record does not exist or it has no transcript_url, we cannot proceed
    if record is None or record.transcript_url is None:
        raise Exception("No transcription record found for ID: " + str(record_id))

    # Prepare local file path for the downloaded transcript_file
    local_transcription_path = os.path.join('/tmp', os.path.basename(record.transcript_url))
    
    # Download the transcription file from S3 to local
    download_from_s3(BUCKET_NAME, record.transcript_url, local_transcription_path)
    
    # Read the transcription text
    with open(local_transcription_path, 'r') as file:
        transcription_text = file.read()

    # Model to use
    model = "gpt-4"

    # Generate notes using GPT model
    response = openai.ChatCompletion.create(
                  model=model,
                  messages=[{"role": "system", "content": 'You are an assistant for creating notes based on transcriptions from films. The notes should include the main theme of the film, plus points and sub-points and be useful for creating content for social media. Answer only in the form of notes in the language you received the text.'},
                            {"role": "user", "content": transcription_text}
                  ])

    # Check if the response is okay and extract the generated text
    if response["choices"][0]["finish_reason"] == 'stop':
        notes = response["choices"][0]["message"]["content"]
    else:
        raise Exception("Error generating notes using " + model)

    # Create S3 connection
    s3 = boto3.resource('s3', aws_access_key_id=S3_ACCESS_KEY, aws_secret_access_key=S3_SECRET_KEY)

    # Save the notes on S3 and update the database record
    notes_file_path = 'notes/' + model + '/' + os.path.basename(local_transcription_path).replace('.txt', '_' + model + '.txt')
    s3.Object(BUCKET_NAME, notes_file_path).put(Body=notes)

    update_notes_record(record.id, notes_file_path, model)

    return notes

@job('default', connection=conn, timeout=3600)
def generate_social_media_content(record_id, content_types):
    # Get the transcription record
    record = get_transcription_record(record_id)
    if record is None:
        raise Exception("No record found with id " + str(record_id))
    
    # Download the notes from S3
    notes_local_path = os.path.join(tempfile.gettempdir(), 'notes.txt')
    download_from_s3(BUCKET_NAME, record.notes_url_gpt4, notes_local_path)
    with open(notes_local_path, 'r') as file:
        notes = file.read()
    
    # Generate social media content using GPT models for each content type
    for model in ['gpt-3.5-turbo', 'gpt-4']:
        for content_type in content_types:
            # Print the type of content being generated and the model
            print(f"Generating {content_type} content using {model}...")
            
            # Prepare the system message
            system_message = f'You are an assistant for creating {content_type} content based on notes about youtube film, describing and encouraging the viewing of the film. Answer only in the language you received the text.'
            
            # Generate social media content using GPT model
            response = openai.ChatCompletion.create(
                          model=model,
                          messages=[{"role": "system", "content": system_message},
                                    {"role": "user", "content": notes}
                          ])

            # Check if the response is okay and extract the generated text
            if response["choices"][0]["finish_reason"] == 'stop':
                content = response["choices"][0]["message"]["content"]
                print(f"Generated content: {content}")
            else:
                raise Exception(f"Error generating {content_type} content using {model}")

            # Update the record
            update_social_media_content_record(record_id, model, content_type, content)
            print(f"Updated {content_type} content for model {model} in database.")
