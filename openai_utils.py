import openai
import os
from dotenv import load_dotenv
from rq.decorators import job
from worker import conn

load_dotenv()

@job('default', connection=conn, timeout=3600)
def transcript(audio_file_path, root_path):
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    audio_file = open(audio_file_path, "rb")
    transcript_data = openai.Audio.transcribe("whisper-1", audio_file, OPENAI_API_KEY)
    text = transcript_data['text']

    transcription_folder = os.path.join(root_path, 'transcriptions')
    os.makedirs(transcription_folder, exist_ok=True)
    
    transcription_file_path = os.path.join(transcription_folder, os.path.basename(audio_file_path) + '.txt')

    with open(transcription_file_path, 'w') as file:
        file.write(text)
        
    return text, transcription_file_path
