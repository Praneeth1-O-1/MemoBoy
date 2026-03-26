"""APScheduler-based reminder scheduling service."""
import logging
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore

logger = logging.getLogger('voicenote.scheduler')

scheduler = BackgroundScheduler(
    jobstores={'default': MemoryJobStore()},
    job_defaults={'coalesce': True, 'max_instances': 1}
)

_app = None


def init_scheduler(app):
    """Initialize the scheduler with the Flask app context."""
    global _app
    _app = app

    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler started successfully")

    # Reschedule any pending reminders from the database
    with app.app_context():
        _reschedule_pending_reminders()


def _reschedule_pending_reminders():
    """Reschedule reminders that haven't been triggered yet (e.g., after server restart)."""
    from app.models import Reminder
    from app import db

    pending = Reminder.query.filter_by(is_triggered=False).all()
    now = datetime.now(timezone.utc)

    for reminder in pending:
        remind_at = reminder.remind_at
        if remind_at.tzinfo is None:
            remind_at = remind_at.replace(tzinfo=timezone.utc)

        if remind_at > now:
            schedule_reminder(reminder.id, remind_at, reminder.message)
            logger.info(f"Rescheduled Reminder #{reminder.id} for {remind_at}")
        else:
            # Mark past-due reminders as triggered
            reminder.is_triggered = True
            logger.info(f"Marked past-due Reminder #{reminder.id} as triggered")

    db.session.commit()


def schedule_reminder(reminder_id: int, remind_at: datetime, message: str):
    """
    Schedule a reminder job to fire at the given time.

    Args:
        reminder_id: The database ID of the reminder.
        remind_at: When to trigger the reminder.
        message: The reminder message.
    """
    job_id = f"reminder_{reminder_id}"

    # Ensure timezone-aware
    if remind_at.tzinfo is None:
        remind_at = remind_at.replace(tzinfo=timezone.utc)

    scheduler.add_job(
        func=_trigger_reminder,
        trigger='date',
        run_date=remind_at,
        id=job_id,
        replace_existing=True,
        args=[reminder_id],
        name=f"Reminder: {message[:50]}"
    )

    logger.info(f"Scheduled Reminder #{reminder_id} for {remind_at.isoformat()}: {message}")


def cancel_reminder(reminder_id: int):
    """Cancel a scheduled reminder job."""
    job_id = f"reminder_{reminder_id}"
    try:
        scheduler.remove_job(job_id)
        logger.info(f"Cancelled Reminder #{reminder_id}")
    except Exception:
        logger.warning(f"No scheduled job found for Reminder #{reminder_id}")


def _trigger_reminder(reminder_id: int):
    """Callback when a reminder fires — marks it as triggered and logs the event."""
    global _app
    if _app is None:
        logger.error("No Flask app context available for reminder trigger")
        return

    with _app.app_context():
        from app.models import Reminder
        from app import db

        reminder = db.session.get(Reminder, reminder_id)
        if not reminder:
            logger.error(f"Reminder #{reminder_id} not found when triggered")
            return

        reminder.is_triggered = True
        db.session.commit()

        logger.info(
            f"🔔 REMINDER TRIGGERED — #{reminder_id}: {reminder.message} "
            f"(Note #{reminder.note_id})"
        )
