"""Tests for the AI intent parser with mock transcripts."""
import json
import pytest
from unittest.mock import patch, MagicMock
from app import create_app, db
from app.services.ai_parser import parse_transcript, _fallback_result


@pytest.fixture
def app():
    """Create test app."""
    app = create_app('testing')
    app.config['GEMINI_API_KEY'] = 'test-key-not-real'
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _mock_gemini_response(content: dict):
    """Create a mock Gemini response."""
    mock_response = MagicMock()
    mock_response.text = json.dumps(content)
    return mock_response


class TestParseTranscript:
    """Test Gemini intent parser with various transcript types."""

    @patch('google.genai.Client')
    def test_simple_note_no_reminder(self, mock_client_cls, app):
        """Test parsing a simple note without any reminder intent."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_client.models.generate_content.return_value = _mock_gemini_response({
            'title': 'Grocery List',
            'summary': 'User listed grocery items: milk, eggs, bread',
            'has_reminder': False,
            'reminder_time': None,
            'reminder_message': None
        })

        with app.app_context():
            result = parse_transcript("I need to buy milk, eggs, and bread from the store")

        assert result['title'] == 'Grocery List'
        assert result['has_reminder'] is False
        assert result['reminder_time'] is None

    @patch('google.genai.Client')
    def test_note_with_reminder(self, mock_client_cls, app):
        """Test parsing a transcript that contains a reminder."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_client.models.generate_content.return_value = _mock_gemini_response({
            'title': 'Call Mom',
            'summary': 'User wants to be reminded to call their mom at 10pm',
            'has_reminder': True,
            'reminder_time': '2099-12-31T22:00:00+00:00',
            'reminder_message': 'Call mom'
        })

        with app.app_context():
            result = parse_transcript("Remind me at 10pm to call mom")

        assert result['title'] == 'Call Mom'
        assert result['has_reminder'] is True
        assert result['reminder_time'] is not None
        assert result['reminder_message'] == 'Call mom'

    @patch('google.genai.Client')
    def test_note_with_implicit_reminder(self, mock_client_cls, app):
        """Test parsing a transcript with an implied reminder but no specific time."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_client.models.generate_content.return_value = _mock_gemini_response({
            'title': 'Pick Up Dry Cleaning',
            'summary': 'User needs to pick up dry cleaning, implied urgency',
            'has_reminder': True,
            'reminder_time': None,
            'reminder_message': "Don't forget to pick up dry cleaning"
        })

        with app.app_context():
            result = parse_transcript("Don't forget to pick up my dry cleaning")

        assert result['has_reminder'] is True
        assert result['reminder_time'] is None
        assert 'dry cleaning' in result['reminder_message'].lower()

    def test_empty_transcript(self, app):
        """Test handling of empty transcript."""
        with app.app_context():
            result = parse_transcript("")

        assert result['title'] == 'Empty Note'
        assert result['has_reminder'] is False

    def test_none_transcript(self, app):
        """Test handling of None transcript."""
        with app.app_context():
            result = parse_transcript(None)

        assert result['title'] == 'Empty Note'

    @patch('google.genai.Client')
    def test_api_error_fallback(self, mock_client_cls, app):
        """Test that API errors produce a graceful fallback result."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_client.models.generate_content.side_effect = Exception("Service unavailable")

        with app.app_context():
            result = parse_transcript("This is a test transcript for fallback")

        assert result['title'] is not None
        assert result['has_reminder'] is False

    @patch('google.genai.Client')
    def test_malformed_json_fallback(self, mock_client_cls, app):
        """Test handling when AI returns invalid JSON."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.text = "This is not JSON"
        mock_client.models.generate_content.return_value = mock_response

        with app.app_context():
            result = parse_transcript("Test transcript for bad JSON")

        assert result['title'] is not None
        assert result['has_reminder'] is False


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
