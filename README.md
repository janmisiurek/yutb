# Yutb: Video to Social Media Content Generator



Yutb is an Flask web application that generates transcriptions from YouTube videos using OpenAI's Whisper model. It then transforms those transcriptions into notes, and eventually into content for various social media platforms using GPT-4.


## Features
1. Transcribes YouTube videos to text.
2. Generates notes from the transcriptions.
3. Creates content for various social media platforms from the notes.
4. User authentication and token-based access system.

## Technologies Used

- Flask: The Python micro web framework.
- OpenAI API: For generating transcriptions and notes.
- Redis Queue (RQ): For managing background jobs.
- PostgreSQL: The database.
- AWS S3: For storing notes and transcriptions.
- Python libraries such as pytube and yt-dlp for handling YouTube videos.
- Other Python libraries such as Authlib, Flask-SQLAlchemy, Flask-Login for additional functionalities.

## Getting Started

### Requirements

Python 3.9+ is required. Make sure all dependencies are installed by running:

```sh
pip install -r requirements.txt
```

## Environment Variables

The application needs several environment variables to function correctly. These variables include the Flask application name, the database URL, the OpenAI API key, AWS credentials, and others.

You will find an `example.env` file in the root of the repository. Make a copy of this file, name it `.env`, and fill in the values for each environment variable:

```sh
cp example.env .env
```

Then, open `.env` with your favorite text editor fill your actual credentials.



## Running the App

Once you've set up everything, start the Flask server by running:

```sh
flask run
```

The application will be accessible at `http://localhost:8000`.

