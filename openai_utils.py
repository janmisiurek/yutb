import openai
import os
from dotenv import load_dotenv
from rq.decorators import job
from worker import conn
import boto3

load_dotenv()
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
BUCKET_NAME = os.getenv('BUCKET_NAME')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


@job('default', connection=conn, timeout=3600)
def transcript(download_audio_output):
    audio_file_path, yt_url = download_audio_output
    audio_file = open(audio_file_path, "rb")
    transcript_data = openai.Audio.transcribe("whisper-1", audio_file, OPENAI_API_KEY)
    text = transcript_data['text']

    transcription_file_path = 'transcriptions/' + os.path.basename(audio_file_path) + '.txt'

    s3 = boto3.resource('s3', aws_access_key_id=S3_ACCESS_KEY, aws_secret_access_key=S3_SECRET_KEY)
    s3.Object(BUCKET_NAME, transcription_file_path).put(Body=text)


    return text, transcription_file_path, audio_file_path, yt_url