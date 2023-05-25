import openai
import os
from dotenv import load_dotenv
from rq.decorators import job
from worker import conn
import boto3

load_dotenv()
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY= os.getenv("SECRET_KEY")
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


@job('default', connection=conn, timeout=3600)
def transcript(download_audio_output):
    audio_file_path, yt_url = download_audio_output
    audio_file = open(audio_file_path, "rb")
    transcript_data = openai.Audio.transcribe("whisper-1", audio_file, OPENAI_API_KEY)
    text = transcript_data['text']

    transcription_file_path = 'transcriptions/' + os.path.basename(audio_file_path) + '.txt'

    s3 = boto3.resource('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
    s3.Object('wiadroborka', transcription_file_path).put(Body=text)

    # Zwróć audio_file_path i yt_url wraz z innymi danymi
    return text, transcription_file_path, audio_file_path, yt_url