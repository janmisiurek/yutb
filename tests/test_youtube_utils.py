import os
import sys
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from unittest.mock import patch, MagicMock

from youtube_utils import download_audio_without_job

def test_simple():
    assert 1 == 1


@patch('youtube_utils.os.makedirs')
@patch('youtube_utils.yt_dlp.YoutubeDL')
@patch('youtube_utils.upload_to_s3')
@patch('youtube_utils.create_audio_record')
def test_directory_creation(create_audio_record_mock, upload_to_s3_mock, ydl_mock, makedirs_mock):
    # Mock 'YoutubeDL' instance methods
    ydl_instance = ydl_mock.return_value.__enter__.return_value
    ydl_instance.extract_info.return_value = {}
    ydl_instance.prepare_filename.return_value = 'download/test.webm'

    download_audio_without_job("http://youtube.com")

    makedirs_mock.assert_called_once_with('download', exist_ok=True)




@patch('youtube_utils.create_audio_record')
@patch('youtube_utils.upload_to_s3')
@patch('youtube_utils.yt_dlp.YoutubeDL')
@patch('youtube_utils.os.makedirs')
def test_audio_record_creation(makedirs_mock, ydl_mock, s3_mock, record_mock):
    ydl_instance = ydl_mock.return_value.__enter__.return_value
    ydl_instance.prepare_filename.return_value = 'download/test.webm'
    ydl_instance.extract_info.return_value = {}
    download_audio_without_job("http://youtube.com")
    name = 'test'
    url = "http://youtube.com"
    output_file = 'download/test.mp3'
    record_mock.assert_called_once()
