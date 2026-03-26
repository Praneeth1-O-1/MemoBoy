# VoiceNote — AI Guidance File

## Project Overview
VoiceNote is an AI-powered voice notes & reminders application. Users record voice notes, which are transcribed using OpenAI Whisper, then parsed by GPT-4o to extract intent and automatically create reminders.

## Architecture

### Backend (Flask + Python)
- **App Factory**: `app/__init__.py` — initializes Flask, SQLAlchemy, CORS, APScheduler
- **Models**: `app/models.py` — User, Note (state machine), Reminder (FK to Note)
- **Services**:
  - `transcription.py` — OpenAI Whisper API for audio-to-text
  - `ai_parser.py` — GPT-4o for intent extraction (title, summary, reminders)
  - `scheduler.py` — APScheduler for background reminder triggering
- **Routes**: RESTful endpoints for notes (CRUD + voice upload) and reminders (list, cancel)
- **Validators**: Audio format validation, future-time enforcement for reminders

### Frontend (React + Vite)
- **Components**: RecordButton (MediaRecorder API), NoteCard, ReminderBadge
- **Pages**: Home (note list + recording), NoteDetail (transcript + reminders)
- **API Client**: Axios-based client for all backend endpoints

## AI Integration Details

### Whisper API (Transcription)
- Model: `whisper-1`
- Accepts: wav, mp3, m4a, webm, ogg, flac
- Output: Plain text transcript
- Error handling: Sets note status to `failed` on API errors

### GPT-4o (Intent Parsing)
- Temperature: 0.1 (deterministic)
- Response format: JSON object mode
- Extracts: title, summary, has_reminder, reminder_time (ISO 8601), reminder_message
- System prompt enforces:
  - Relative time parsing against provided current time
  - Strict JSON-only responses
  - Graceful handling of ambiguous intents

### Prompt Engineering Constraints
1. Always provide current UTC time for relative time resolution
2. Use `response_format: json_object` to guarantee valid JSON
3. Low temperature (0.1) for consistent, deterministic parsing
4. Fallback to basic extraction if AI fails (title from first 50 chars, no reminder)
5. Validate AI output fields before using — never trust raw AI response blindly

## Note Status State Machine
```
pending_transcription → transcribed → reminder_set
                     ↘ failed
```

## Database Constraints
- A Reminder **cannot exist** without a Note (FK constraint, cascade delete)
- Reminder times **must be in the future** (validated at API level)
- Note audio files are cleaned up on deletion

## Coding Conventions
- Python: PEP 8, type hints, comprehensive logging
- React: Functional components with hooks, no class components
- All API errors return JSON with `error` field
- Tests mock OpenAI API calls — no real API key needed for testing
