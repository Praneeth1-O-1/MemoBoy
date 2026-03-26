"""Local intent extraction service for parsing voice note transcripts (no API required)."""

import logging
from datetime import datetime, timezone

logger = logging.getLogger('voicenote.ai_parser')


def parse_transcript(transcript: str, current_time: datetime | None = None) -> dict:
    """
    Parse a voice note transcript to extract intent and reminders (local rule-based).
    """

    if not transcript or not transcript.strip():
        logger.warning("Empty transcript provided to parser")
        return {
            'title': 'Empty Note',
            'summary': '',
            'has_reminder': False,
            'reminder_time': None,
            'reminder_message': None
        }

    if current_time is None:
        current_time = datetime.now(timezone.utc)

    logger.info(f"Parsing transcript locally ({len(transcript)} chars)")

    try:
        result = _rule_based_parser(transcript, current_time)

        logger.info(
            f"Parsed result: title='{result['title']}', has_reminder={result['has_reminder']}"
        )
        return result

    except Exception as e:
        logger.error(f"Error during transcript parsing: {type(e).__name__}: {e}")
        return _fallback_result(transcript)


# -----------------------------
# Rule-based parser (core logic)
# -----------------------------
def _rule_based_parser(transcript: str, current_time: datetime) -> dict:
    text = transcript.lower()

    # Detect reminder intent
    reminder_keywords = [
        "remind", "don't forget", "remember",
        "tomorrow", "later", "tonight", "today",
        "at", "pm", "am"
    ]

    has_reminder = any(keyword in text for keyword in reminder_keywords)

    # Very basic time detection (can improve later)
    reminder_time = None
    if "tomorrow" in text:
        from datetime import timedelta
        reminder_time = (current_time + timedelta(days=1)).isoformat()

    # Extract title (first meaningful part)
    title = transcript[:50].strip()
    if len(transcript) > 50:
        title += "..."

    # Summary (simple truncation)
    summary = transcript[:200]

    return {
        'title': title,
        'summary': summary,
        'has_reminder': has_reminder,
        'reminder_time': reminder_time,
        'reminder_message': transcript if has_reminder else None
    }


# -----------------------------
# Fallback (safe default)
# -----------------------------
def _fallback_result(transcript: str) -> dict:
    return {
        'title': transcript[:50].strip() + ('...' if len(transcript) > 50 else ''),
        'summary': transcript[:200],
        'has_reminder': False,
        'reminder_time': None,
        'reminder_message': None
    }