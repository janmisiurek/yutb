import openai
import os
from dotenv import load_dotenv
from rq.decorators import job
from worker import conn
import boto3
from tasks import update_transcript_record, get_audio_record
from aws_utils import download_from_s3

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
    update_transcript_record(record.yt_url, transcription_file_path)

    return text