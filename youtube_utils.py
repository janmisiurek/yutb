from pytube import YouTube
from rq.decorators import job
from worker import conn

@job('default', connection=conn, timeout=3600)
def download_audio(url):
    yt = YouTube(url)
    audio_stream = yt.streams.filter(only_audio=True).first()
    output_file = audio_stream.download(output_path='download')
    return output_file
