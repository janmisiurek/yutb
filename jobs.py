from rq.decorators import job
from worker import conn
from youtube_utils import download_audio
from openai_utils import transcript, generate_notes

# Helper function combines the download, transcript, and create_notes functions for asynchronous execution as an RQ job
@job('default', connection=conn, timeout=7200)
def download_transcribe_generate_notes(url, tempo):
    record_id = download_audio(url, tempo)
    transcript(record_id)
    return generate_notes(record_id)
