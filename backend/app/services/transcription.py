from sarvamai import SarvamAI
import os
import json
import shutil
from flask import current_app



def transcribe_audio(note_id: int) -> str | None:
    from app import db
    from app.models import Note

    api_key = os.getenv("SARVAM_API_KEY")

    if not api_key:
        print("❌ SARVAM_API_KEY missing")
        return None

    client = SarvamAI(api_subscription_key=api_key)

    note = db.session.get(Note, note_id)
    if not note:
        return None

    try:
        # Create job
        job = client.speech_to_text_job.create_job(
            model="saaras:v3",
            mode="transcribe",
            language_code="unknown"
        )

        # Upload file
        job.upload_files(file_paths=[note.audio_path])

        # Start job
        job.start()

        # Wait (blocking for now — we'll fix later)
        job.wait_until_complete()

        # Get results
        results = job.get_file_results()

        if not results["successful"]:
            note.status = Note.STATUS_FAILED
            db.session.commit()
            return None

        # Download output
        temp_dir = os.path.join(current_app.root_path, "temp_outputs", f"job_{note_id}")
        os.makedirs(temp_dir, exist_ok=True)
        job.download_outputs(output_dir=temp_dir)

        transcript = ""

        try:
            for file in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file)

                with open(file_path) as f:
                    data = json.load(f)

                    if data.get("transcript"):
                        transcript = data["transcript"]
                        break
        finally:
            # Clean up the temp directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

        if not transcript:
            note.status = Note.STATUS_FAILED
            db.session.commit()
            return None

        # Save
        note.transcript = transcript
        note.status = Note.STATUS_TRANSCRIBED

        if not note.title:
            note.title = transcript[:50] + "..."

        db.session.commit()

        return transcript

    except Exception as e:
        print("Sarvam error:", e)
        note.status = Note.STATUS_FAILED
        db.session.commit()
        return None