"""Tests for notes routes."""
import io
import json
import pytest
from app import create_app, db
from app.models import Note, Reminder


@pytest.fixture
def app():
    """Create test app."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client."""
    return app.test_client()


class TestListNotes:
    """Tests for GET /notes."""

    def test_list_notes_empty(self, client):
        response = client.get('/notes')
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data['notes'] == []
        assert data['total'] == 0

    def test_list_notes_with_data(self, client, app):
        with app.app_context():
            note = Note(audio_path='/tmp/test.wav', title='Test Note', status='transcribed')
            db.session.add(note)
            db.session.commit()

        response = client.get('/notes')
        data = json.loads(response.data)
        assert response.status_code == 200
        assert len(data['notes']) == 1
        assert data['notes'][0]['title'] == 'Test Note'

    def test_list_notes_pagination(self, client, app):
        with app.app_context():
            for i in range(5):
                note = Note(audio_path=f'/tmp/test{i}.wav', title=f'Note {i}', status='transcribed')
                db.session.add(note)
            db.session.commit()

        response = client.get('/notes?per_page=2&page=1')
        data = json.loads(response.data)
        assert len(data['notes']) == 2
        assert data['total'] == 5
        assert data['pages'] == 3


class TestGetNote:
    """Tests for GET /notes/<id>."""

    def test_get_note_exists(self, client, app):
        with app.app_context():
            note = Note(audio_path='/tmp/test.wav', title='My Note', transcript='Hello world', status='transcribed')
            db.session.add(note)
            db.session.commit()
            note_id = note.id

        response = client.get(f'/notes/{note_id}')
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data['note']['title'] == 'My Note'
        assert data['note']['transcript'] == 'Hello world'

    def test_get_note_not_found(self, client):
        response = client.get('/notes/9999')
        assert response.status_code == 404


class TestDeleteNote:
    """Tests for DELETE /notes/<id>."""

    def test_delete_note(self, client, app):
        with app.app_context():
            note = Note(audio_path='/tmp/nonexistent.wav', title='Delete Me', status='transcribed')
            db.session.add(note)
            db.session.commit()
            note_id = note.id

        response = client.delete(f'/notes/{note_id}')
        assert response.status_code == 200

        response = client.get(f'/notes/{note_id}')
        assert response.status_code == 404

    def test_delete_note_not_found(self, client):
        response = client.delete('/notes/9999')
        assert response.status_code == 404


class TestUploadVoice:
    """Tests for POST /notes/voice."""

    def test_upload_no_file(self, client):
        response = client.post('/notes/voice')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_upload_invalid_extension(self, client):
        data = {'audio': (io.BytesIO(b'not audio'), 'test.txt')}
        response = client.post('/notes/voice', data=data, content_type='multipart/form-data')
        assert response.status_code == 400


class TestCreateReminder:
    """Tests for POST /notes/<id>/remind."""

    def test_create_reminder_no_note(self, client):
        response = client.post('/notes/9999/remind',
                               data=json.dumps({'remind_at': '2099-12-31T23:59:00', 'message': 'Test'}),
                               content_type='application/json')
        assert response.status_code == 404

    def test_create_reminder_no_body(self, client, app):
        with app.app_context():
            note = Note(audio_path='/tmp/test.wav', status='transcribed')
            db.session.add(note)
            db.session.commit()
            note_id = note.id

        response = client.post(f'/notes/{note_id}/remind',
                               data=json.dumps({}),
                               content_type='application/json')
        assert response.status_code == 400

    def test_create_reminder_past_time(self, client, app):
        with app.app_context():
            note = Note(audio_path='/tmp/test.wav', status='transcribed')
            db.session.add(note)
            db.session.commit()
            note_id = note.id

        response = client.post(f'/notes/{note_id}/remind',
                               data=json.dumps({'remind_at': '2020-01-01T00:00:00', 'message': 'Too late'}),
                               content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'future' in data['error'].lower()

    def test_create_reminder_success(self, client, app):
        with app.app_context():
            note = Note(audio_path='/tmp/test.wav', status='transcribed')
            db.session.add(note)
            db.session.commit()
            note_id = note.id

        response = client.post(f'/notes/{note_id}/remind',
                               data=json.dumps({'remind_at': '2099-12-31T23:59:00', 'message': 'Future reminder'}),
                               content_type='application/json')
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['reminder']['message'] == 'Future reminder'
