from rq.decorators import job
from worker import conn
from aws_utils import upload_to_s3
import os
import yt_dlp



import os
import yt_dlp
from rq.decorators import job

@job('default', connection=conn, timeout=3600)
def download_audio(url):
    output_dir = 'download'
    os.makedirs(output_dir, exist_ok=True)

    # Define options for yt-dlp
    options = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(id)s.%(ext)s'),
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
        output_file = ydl.prepare_filename(info_dict)

    print('sending file to s3')
    output_s3_key = os.path.join(output_dir, info_dict['id'] + '.mp3')

    print(f"Current working directory: {os.getcwd()}")

    # Upload file to S3
    upload_to_s3(output_file, 'wiadroborka', object_name=output_s3_key)

    return output_file, url
