from pytube import YouTube
from rq.decorators import job
from worker import conn
from aws_utils import upload_to_s3
import os

@job('default', connection=conn, timeout=3600)
def download_audio(url):
    yt = YouTube(url)
    audio_stream = yt.streams.filter(only_audio=True).first()
    output_dir = 'download'
    os.makedirs(output_dir, exist_ok=True)
    output_file = audio_stream.download(output_path=output_dir)

    # Extract filename from the full file path
    output_file_name = os.path.basename(output_file)
    output_s3_key = os.path.join(output_dir, output_file_name)
    print('sending file to s3')
    # Upload file to S3
    upload_to_s3(output_file, 'wiadroborka', object_name=output_s3_key)

    return output_file, url

