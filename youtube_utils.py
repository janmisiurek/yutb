from pytube import YouTube
from rq.decorators import job
from worker import conn
import os

@job('default', connection=conn, timeout=3600)
def download_audio(url):
    yt = YouTube(url)
    audio_stream = yt.streams.filter(only_audio=True).first()
    output_dir = 'download'
    os.makedirs(output_dir, exist_ok=True)  # utwórz katalog, jeśli nie istnieje
    output_file = audio_stream.download(output_path=output_dir)
    return output_file