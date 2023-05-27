from rq.decorators import job
from worker import conn
from aws_utils import upload_to_s3
import os
import yt_dlp
import openai_utils

def clean_title(title):
    return "".join(c for c in title if c.isalnum() or c in (' ', '.', '_')).rstrip()

@job('default', connection=conn, timeout=3600)
def download_audio(url):
    output_dir = 'download'
    os.makedirs(output_dir, exist_ok=True)

    # Define options for yt-dlp
    options = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
            'nopostoverwrites': False,
        }],
    }

    # Download the audio
    with yt_dlp.YoutubeDL(options) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        # Prepare the output file name by replacing the extension with .mp3
        output_file = ydl.prepare_filename(info_dict).replace('.webm', '.mp3')
        clean_file_name = clean_title(output_file)

    print('sending file to s3')
    output_s3_key = os.path.join(output_dir, clean_file_name)

    # Upload file to S3
    upload_to_s3(clean_file_name, 'wiadroborka', object_name=output_s3_key)

    return clean_file_name, url
