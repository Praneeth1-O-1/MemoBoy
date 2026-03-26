"""Reminders routes — list and cancel reminders."""
import logging
from flask import Blueprint, jsonify, request
from app import db
from app.models import Reminder, Note
from app.services.scheduler import cancel_reminder, schedule_reminder
from app.utils.validators import validate_reminder_time, validate_reminder_message

logger = logging.getLogger('voicenote.routes.reminders')

reminders_bp = Blueprint('reminders', __name__)


@reminders_bp.route('', methods=['GET'])
def list_reminders():
    """List all upcoming (non-triggered) reminders."""
    reminders = Reminder.query.filter_by(is_triggered=False)\
        .order_by(Reminder.remind_at.asc()).all()

    return jsonify({
        'reminders': [r.to_dict() for r in reminders],
        'count': len(reminders)
    })


@reminders_bp.route('/all', methods=['GET'])
def list_all_reminders():
    """List all reminders including triggered ones."""
    reminders = Reminder.query.order_by(Reminder.remind_at.desc()).all()

    return jsonify({
        'reminders': [r.to_dict() for r in reminders],
        'count': len(reminders)
    })


@reminders_bp.route('/<int:reminder_id>', methods=['DELETE'])
def delete_reminder(reminder_id):
    """Cancel and delete a reminder."""
    reminder = db.session.get(Reminder, reminder_id)
    if not reminder:
        return jsonify({'error': 'Reminder not found'}), 404

    # Cancel scheduled job
    cancel_reminder(reminder_id)

    db.session.delete(reminder)
    db.session.commit()

    logger.info(f"Deleted Reminder #{reminder_id}")
    return jsonify({'message': f'Reminder #{reminder_id} cancelled and deleted'}), 200


@reminders_bp.route('', methods=['POST'])
def create_standalone_reminder():
    """Create a standalone reminder (not attached to a specific voice note)."""
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

    # Find or create standalone anchor note
    anchor_note = Note.query.filter_by(status='standalone').first()
    if not anchor_note:
        anchor_note = Note(title="Standalone Reminders", audio_path="none", status="standalone")
        db.session.add(anchor_note)
        db.session.flush() # flush to get id

    reminder = Reminder(
        note_id=anchor_note.id,
        remind_at=remind_at,
        message=message
    )

    db.session.add(reminder)
    db.session.commit()

    schedule_reminder(reminder.id, remind_at, message)
    logger.info(f"Created Standalone Reminder #{reminder.id}")

    return jsonify({
        'message': 'Standalone reminder created',
        'reminder': reminder.to_dict()
    }), 201


@reminders_bp.route('/<int:reminder_id>/toggle', methods=['PATCH'])
def toggle_reminder_status(reminder_id):
    """Toggle the is_triggered status of a reminder."""
    reminder = db.session.get(Reminder, reminder_id)
    if not reminder:
        return jsonify({'error': 'Reminder not found'}), 404

    # Toggle
    reminder.is_triggered = not reminder.is_triggered
    db.session.commit()

    if reminder.is_triggered:
        cancel_reminder(reminder.id)
    else:
        # Re-schedule if marked as not done and time is in future
        import datetime
        from datetime import timezone
        if reminder.remind_at > datetime.datetime.now(timezone.utc):
            schedule_reminder(reminder.id, reminder.remind_at, reminder.message)

    return jsonify({
        'message': 'Reminder status toggled',
        'reminder': reminder.to_dict()
    }), 200
