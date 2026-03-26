import pytest
from datetime import datetime, timezone
from app.services.ai_parser import parse_transcript, _fallback_result

class TestParseTranscript:
    """Test local rule-based intent parser."""

    def test_simple_note_no_reminder(self):
        """Test parsing a simple note without any reminder intent."""
        result = parse_transcript("I need to buy milk, eggs, and bread from the store")

        assert result['title'] == 'I need to buy milk, eggs, and bread from the store'
        assert result['has_reminder'] is False
        assert result['reminder_time'] is None
        assert result['reminder_message'] is None

    def test_note_with_reminder(self):
        """Test parsing a transcript that contains a reminder."""
        result = parse_transcript("Remind me tomorrow to call mom")

        assert result['title'] == 'Remind me tomorrow to call mom'
        assert result['has_reminder'] is True
        assert result['reminder_time'] is not None
        assert result['reminder_message'] == 'Remind me tomorrow to call mom'

    def test_note_with_implicit_reminder(self):
        """Test parsing a transcript with an implied reminder but no specific time."""
        result = parse_transcript("Don't forget to pick up my dry cleaning")

        assert result['title'] == "Don't forget to pick up my dry cleaning"
        assert result['has_reminder'] is True
        assert result['reminder_time'] is None
        assert result['reminder_message'] == "Don't forget to pick up my dry cleaning"

    def test_empty_transcript(self):
        """Test handling of empty transcript."""
        result = parse_transcript("")

        assert result['title'] == 'Empty Note'
        assert result['has_reminder'] is False

    def test_none_transcript(self):
        """Test handling of None transcript."""
        result = parse_transcript(None)

        assert result['title'] == 'Empty Note'

class TestFallbackResult:
    """Test the fallback result generator."""

    def test_short_transcript(self):
        result = _fallback_result("Short note")
        assert result['title'] == 'Short note'
        assert result['has_reminder'] is False

    def test_long_transcript(self):
        long_text = "x" * 100
        result = _fallback_result(long_text)
        assert len(result['title']) <= 53  # 50 chars + '...'
        assert result['title'].endswith('...')

    def test_summary_truncated(self):
        long_text = "y" * 300
        result = _fallback_result(long_text)
        assert len(result['summary']) <= 200
