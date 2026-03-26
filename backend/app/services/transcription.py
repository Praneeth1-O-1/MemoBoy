import logging
import traceback
import subprocess
import os
from flask import current_app
from app import db
from app.models import Note

from faster_whisper import WhisperModel

logger = logging.getLogger('voicenote.transcription')

# Load model once (IMPORTANT: don't load per request)
model = WhisperModel("base", device="cpu", compute_type="int8")


def convert_to_wav(input_path: str) -> str:
    """Convert audio to wav (16kHz mono) for Whisper."""
    output_path = input_path.rsplit(".", 1)[0] + ".wav"

    subprocess.run([
        "ffmpeg", "-y",
        "-i", input_path,
        "-ar", "16000",
        "-ac", "1",
        output_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return output_path


def transcribe_audio(note_id: int) -> str | None:
    note = db.session.get(Note, note_id)
    if not note:
        logger.error(f"Note #{note_id} not found for transcription")
        return None

    logger.info(f"Starting transcription for Note #{note_id} — file: {note.audio_path}")

    try:
        # Ensure file exists
        if not os.path.exists(note.audio_path):
            logger.error(f"Audio file not found: {note.audio_path}")
            note.status = Note.STATUS_FAILED
            db.session.commit()
            return None

        # Convert to wav (Whisper works best with wav)
        wav_path = convert_to_wav(note.audio_path)

        # Transcribe
        segments, info = model.transcribe(wav_path)

        transcript = " ".join([segment.text for segment in segments]).strip()

        if not transcript:
            logger.warning(f"Empty transcript for Note #{note_id}")
            note.status = Note.STATUS_FAILED
            db.session.commit()
            return None

        # Save result
        note.transcript = transcript
        note.status = Note.STATUS_TRANSCRIBED

        if not note.title:
            note.title = transcript[:50].strip() + ('...' if len(transcript) > 50 else '')

        db.session.commit()

        logger.info(f"Transcription complete for Note #{note_id}: {len(transcript)} chars")
        return transcript

    except Exception as e:
        logger.error(f"Error transcribing Note #{note_id}: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())

        note.status = Note.STATUS_FAILED
        db.session.commit()
        return None