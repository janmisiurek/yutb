from rq.decorators import job
from worker import conn
from youtube_utils import download_audio
from openai_utils import transcript


# Helper function combines the download and transcript functions for asynchronous execution as an RQ job
@job('default', connection=conn, timeout=7200)
def download_and_transcribe(url, tempo):
    record_id = download_audio(url, tempo)
    return transcript(record_id)