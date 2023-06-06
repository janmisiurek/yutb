from rq.decorators import job
from worker import conn
from aws_utils import upload_to_s3
from dotenv import load_dotenv
import os
import yt_dlp
from tasks import create_audio_record
import subprocess

load_dotenv()
BUCKET_NAME = os.getenv('BUCKET_NAME')


def download_audio_without_job(url, tempo):
    output_dir = 'download'
    os.makedirs(output_dir, exist_ok=True)

    # Define options for yt-dlp
    options = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'postprocessors': [
            {
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '96',
            'nopostoverwrites': False,
            },
        ],
    }

    # Download the audio
    with yt_dlp.YoutubeDL(options) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        output_file = ydl.prepare_filename(info_dict).replace('.webm', '.mp3')

    # Change audio tempo using ffmpeg
    tempo_output_file = output_file.replace('.mp3', f'_tempo_{tempo}.mp3')
    command = ['ffmpeg', '-i', output_file, '-filter:a', f'atempo={tempo}', tempo_output_file]
    subprocess.run(command, check=True)

    print('sending file to s3')
    output_s3_key = os.path.join(output_dir, tempo_output_file)

    # Upload file to S3
    upload_to_s3(tempo_output_file, BUCKET_NAME, object_name=tempo_output_file)

    # Create a new record in the database
    name = os.path.splitext(os.path.basename(tempo_output_file))[0]
    record_id = create_audio_record(name, url, tempo_output_file)

    return record_id


           



@job('default', connection=conn, timeout=3600)
def download_audio(url, tempo):
    return download_audio_without_job(url, tempo)