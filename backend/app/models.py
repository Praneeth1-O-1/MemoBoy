"""Database models for VoiceNote."""
from datetime import datetime, timezone
from app import db


class User(db.Model):
    """User model."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    notes = db.relationship('Note', backref='user', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }


class Note(db.Model):
    """Voice note model with state machine for transcription status."""
    __tablename__ = 'notes'

    # Status constants
    STATUS_PENDING = 'pending_transcription'
    STATUS_TRANSCRIBED = 'transcribed'
    STATUS_REMINDER_SET = 'reminder_set'
    STATUS_FAILED = 'failed'

    VALID_STATUSES = [STATUS_PENDING, STATUS_TRANSCRIBED, STATUS_REMINDER_SET, STATUS_FAILED]

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=True)
    audio_path = db.Column(db.String(500), nullable=False)
    transcript = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default=STATUS_PENDING, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    reminders = db.relationship('Reminder', backref='note', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        import os
        audio_filename = os.path.basename(self.audio_path) if self.audio_path else None
        
        created_dt = self.created_at
        if created_dt and created_dt.tzinfo is None:
            created_dt = created_dt.replace(tzinfo=timezone.utc)

        return {
            'id': self.id,
            'title': self.title or f'Voice Note #{self.id}',
            'audio_path': self.audio_path,
            'audio_filename': audio_filename,
            'transcript': self.transcript,
            'status': self.status,
            'created_at': created_dt.isoformat() if created_dt else None,
            'user_id': self.user_id,
            'reminders': [r.to_dict() for r in self.reminders]
        }


class Reminder(db.Model):
    """Reminder model — tied to a note via foreign key."""
    __tablename__ = 'reminders'

    id = db.Column(db.Integer, primary_key=True)
    note_id = db.Column(db.Integer, db.ForeignKey('notes.id'), nullable=False)
    remind_at = db.Column(db.DateTime, nullable=False)
    message = db.Column(db.String(500), nullable=False)
    is_triggered = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        created_dt = self.created_at
        if created_dt and created_dt.tzinfo is None:
            created_dt = created_dt.replace(tzinfo=timezone.utc)
            
        remind_dt = self.remind_at
        if remind_dt and remind_dt.tzinfo is None:
            remind_dt = remind_dt.replace(tzinfo=timezone.utc)

        return {
            'id': self.id,
            'note_id': self.note_id,
            'remind_at': remind_dt.isoformat() if remind_dt else None,
            'message': self.message,
            'is_triggered': self.is_triggered,
            'created_at': created_dt.isoformat() if created_dt else None
        }
