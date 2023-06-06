import openai
import os
from dotenv import load_dotenv
from rq.decorators import job
from worker import conn
import boto3
from tasks import update_transcript_record, get_audio_record
from aws_utils import download_from_s3
import subprocess

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

    # Check the file size
    audio_file_size = os.path.getsize(local_audio_path) / (1024 * 1024)  # size in MB

    # If the file is bigger than 24MB, divide it into chunks
    if audio_file_size >= 24:
        print("Audio file is larger than 24MB. Splitting into chunks.")
        # Define chunk duration in seconds
        chunk_duration = 1500 #25min
        output_format = os.path.splitext(local_audio_path)[1]
        split_audio(local_audio_path, chunk_duration, output_format)
        local_audio_path = glob.glob(local_audio_path + "/*")

    print('Transcribing')
    if isinstance(local_audio_path, list):
        transcripts = []
        for path in local_audio_path:
            with open(path, "rb") as audio_file:
                transcript_data = openai.Audio.transcribe("whisper-1", audio_file, OPENAI_API_KEY)
                transcripts.append(transcript_data['text'])
        text = " ".join(transcripts)
    else:
        with open(local_audio_path, "rb") as audio_file:
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


def split_audio(audio_path, chunk_duration, output_format):

    command = ["ffmpeg", "-i", audio_path, "-f", "segment", "-segment_time", str(chunk_duration),
               "-c", "copy", audio_path + "_%03d" + output_format]
    subprocess.call(command)