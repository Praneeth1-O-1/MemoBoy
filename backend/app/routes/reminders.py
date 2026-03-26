"""Reminders routes — list and cancel reminders."""
import logging
from flask import Blueprint, jsonify
from app import db
from app.models import Reminder
from app.services.scheduler import cancel_reminder

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
