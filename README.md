# VoiceNote 🎙️

AI-Powered Voice Notes & Reminders — Record, transcribe, and get smart reminders from your voice.

## Features

- 🎙️ **Voice Recording** — Record notes directly from your browser
- 🤖 **AI Transcription** — Whisper API converts speech to text
- 🧠 **Intent Parsing** — GPT-4o extracts tasks and reminders from transcripts
- ⏰ **Smart Reminders** — Auto-creates reminders when you say "remind me..."
- 📋 **Note Management** — List, view, and manage all your voice notes

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python + Flask |
| Frontend | React (Vite) |
| Database | SQLite |
| Transcription | OpenAI Whisper API |
| AI Parsing | GPT-4o |
| Scheduling | APScheduler |

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenAI API key

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run the server
python run.py
```

Backend runs at `http://localhost:5000`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/notes/voice` | Upload audio, transcribe, parse intent |
| GET | `/notes` | List all notes |
| GET | `/notes/:id` | Get note detail |
| DELETE | `/notes/:id` | Delete a note |
| POST | `/notes/:id/remind` | Create manual reminder |
| GET | `/reminders` | List upcoming reminders |
| DELETE | `/reminders/:id` | Cancel a reminder |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Your OpenAI API key (required) |
| `FLASK_ENV` | `development` or `production` |
| `SECRET_KEY` | Flask secret key |
| `DATABASE_URL` | Database connection string |

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

Tests use mocked OpenAI responses — no API key required.

## Project Structure

```
voicenote/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Flask app factory
│   │   ├── models.py            # DB models (Note, Reminder, User)
│   │   ├── routes/
│   │   │   ├── notes.py         # /notes endpoints
│   │   │   └── reminders.py     # /reminders endpoints
│   │   ├── services/
│   │   │   ├── transcription.py # Whisper API
│   │   │   ├── ai_parser.py     # GPT-4o intent extraction
│   │   │   └── scheduler.py     # APScheduler jobs
│   │   └── utils/
│   │       └── validators.py    # Input validation
│   ├── tests/
│   ├── config.py
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── components/          # RecordButton, NoteCard, ReminderBadge
│   │   ├── pages/               # Home, NoteDetail
│   │   ├── api/client.js        # Axios API client
│   │   └── App.jsx
│   └── package.json
├── claude.md
└── README.md
```
