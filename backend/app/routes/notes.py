"""Notes routes — voice upload, listing, detail, and reminder creation."""

import os
import uuid
import logging
import threading
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, current_app, send_from_directory

from app import db
from app.models import Note, Reminder
from app.utils.validators import (
    validate_audio_file,
    validate_reminder_time,
    validate_reminder_message
)
from app.services.transcription import transcribe_audio
from app.services.ai_parser import parse_transcript
from app.services.scheduler import schedule_reminder

logger = logging.getLogger('voicenote.routes.notes')

notes_bp = Blueprint('notes', __name__)


# -----------------------------
# Background worker
# -----------------------------
def run_transcription(app, note_id):
    with app.app_context():
        try:
            logger.info(f"Starting background processing for Note #{note_id}")

            transcript = transcribe_audio(note_id)

            if not transcript:
                logger.warning(f"No transcript for Note #{note_id}")
                return

            note = db.session.get(Note, note_id)

            parsed = parse_transcript(transcript)

            # Update title
            if parsed.get('title'):
                note.title = parsed['title']

            # Handle reminder
            if (
                parsed.get('has_reminder')
                and parsed.get('reminder_time')
                and parsed.get('reminder_message')
            ):
                try:
                    remind_at = datetime.fromisoformat(
                        parsed['reminder_time'].replace('Z', '+00:00')
                    )

                    if remind_at.tzinfo is None:
                        remind_at = remind_at.replace(tzinfo=timezone.utc)

                    now = datetime.now(timezone.utc)

                    if remind_at > now:
                        reminder = Reminder(
                            note_id=note.id,
                            remind_at=remind_at,
                            message=parsed['reminder_message']
                        )
                        db.session.add(reminder)
                        note.status = Note.STATUS_REMINDER_SET
                        db.session.commit()

                        schedule_reminder(
                            reminder.id,
                            remind_at,
                            reminder.message
                        )

                        logger.info(
                            f"Auto-created Reminder #{reminder.id} for Note #{note.id}"
                        )

                except Exception as e:
                    logger.warning(f"Reminder parsing failed: {e}")

            db.session.commit()
            logger.info(f"Background processing completed for Note #{note_id}")

        except Exception as e:
            logger.error(f"Background transcription error: {e}")


# -----------------------------
# Routes
# -----------------------------
@notes_bp.route('/voice', methods=['POST'])
def upload_voice_note():
    """Upload an audio file and trigger background processing."""

    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided. Use field name "audio".'}), 400

    audio_file = request.files['audio']

    # Validate file
    is_valid, error = validate_audio_file(audio_file)
    if not is_valid:
        return jsonify({'error': error}), 400

    # Save file
    ext = audio_file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    audio_file.save(filepath)

    logger.info(f"Audio saved: {filepath}")

    # Create note
    note = Note(
        audio_path=filepath,
        status=Note.STATUS_PENDING
    )
    db.session.add(note)
    db.session.commit()

    logger.info(f"Created Note #{note.id}")

    # Start background transcription
    threading.Thread(
        target=run_transcription,
        args=(current_app._get_current_object(), note.id)
    ).start()

    # IMPORTANT: Always return response
    return jsonify({
        'message': 'Voice note uploaded and processing',
        'note': note.to_dict()
    }), 201


@notes_bp.route('/audio/<filename>', methods=['GET'])
def serve_audio(filename):
    """Serve an audio file from uploads."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)


@notes_bp.route('', methods=['GET'])
def list_notes():
    """List notes."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    pagination = Note.query.order_by(Note.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    return jsonify({
        'notes': [n.to_dict() for n in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages
    })


@notes_bp.route('/<int:note_id>', methods=['GET'])
def get_note(note_id):
    """Get single note."""
    note = db.session.get(Note, note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404

    return jsonify({'note': note.to_dict()})


@notes_bp.route('/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete note."""
    note = db.session.get(Note, note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404

    if os.path.exists(note.audio_path):
        os.remove(note.audio_path)
        logger.info(f"Deleted audio file: {note.audio_path}")

    db.session.delete(note)
    db.session.commit()

    logger.info(f"Deleted Note #{note_id}")
    return jsonify({'message': f'Note #{note_id} deleted'}), 200


@notes_bp.route('/<int:note_id>/remind', methods=['POST'])
def create_reminder(note_id):
    """Create reminder manually."""
    note = db.session.get(Note, note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    is_valid, error, remind_at = validate_reminder_time(data.get('remind_at', ''))
    if not is_valid:
        return jsonify({'error': error}), 400

    message = data.get('message', '').strip()
    is_valid, error = validate_reminder_message(message)
    if not is_valid:
        return jsonify({'error': error}), 400

    reminder = Reminder(
        note_id=note.id,
        remind_at=remind_at,
        message=message
    )

    db.session.add(reminder)
    note.status = Note.STATUS_REMINDER_SET
    db.session.commit()

    schedule_reminder(reminder.id, remind_at, message)

    logger.info(f"Created Reminder #{reminder.id} for Note #{note_id}")

    return jsonify({
        'message': 'Reminder created',
        'reminder': reminder.to_dict()
    }), 201