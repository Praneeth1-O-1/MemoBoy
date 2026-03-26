"""Input validation helpers for VoiceNote."""
from datetime import datetime, timezone


ALLOWED_AUDIO_EXTENSIONS = {'wav', 'mp3', 'm4a', 'webm', 'ogg', 'flac'}
ALLOWED_AUDIO_MIMETYPES = {
    'audio/wav', 'audio/x-wav', 'audio/mpeg', 'audio/mp3',
    'audio/mp4', 'audio/x-m4a', 'audio/webm', 'audio/ogg',
    'audio/flac', 'audio/x-flac'
}


def validate_audio_file(file) -> tuple[bool, str]:
    """
    Validate an uploaded audio file.

    Args:
        file: The uploaded file object from Flask request.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if file is None:
        return False, "No file provided"

    if file.filename == '':
        return False, "No file selected"

    # Check extension
    ext = _get_extension(file.filename)
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        return False, f"Invalid audio format '.{ext}'. Allowed: {', '.join(sorted(ALLOWED_AUDIO_EXTENSIONS))}"

    # Check MIME type if available
    if file.content_type and file.content_type not in ALLOWED_AUDIO_MIMETYPES:
        # Be lenient — some browsers send wrong MIME types
        pass

    return True, ""


def validate_reminder_time(remind_at_str: str) -> tuple[bool, str, datetime | None]:
    """
    Validate and parse a reminder time string.

    Args:
        remind_at_str: ISO 8601 datetime string.

    Returns:
        Tuple of (is_valid, error_message, parsed_datetime).
    """
    if not remind_at_str:
        return False, "Reminder time is required", None

    try:
        remind_at = datetime.fromisoformat(remind_at_str.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return False, "Invalid datetime format. Use ISO 8601 (e.g., 2024-12-31T23:59:00)", None

    # Make timezone-aware if naive
    if remind_at.tzinfo is None:
        remind_at = remind_at.replace(tzinfo=timezone.utc)

    # Check if in the past
    now = datetime.now(timezone.utc)
    if remind_at <= now:
        return False, "Reminder time must be in the future", None

    return True, "", remind_at


def validate_reminder_message(message: str) -> tuple[bool, str]:
    """Validate a reminder message."""
    if not message or not message.strip():
        return False, "Reminder message cannot be empty"

    if len(message) > 500:
        return False, "Reminder message must be 500 characters or less"

    return True, ""


def _get_extension(filename: str) -> str:
    """Extract lowercase file extension from filename."""
    if '.' not in filename:
        return ''
    return filename.rsplit('.', 1)[1].lower()
