/**
 * NoteDetail — Single note view with audio player, transcript, reminders, and manual reminder creation.
 */
import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchNote, createReminder, deleteNote, deleteReminder, toggleReminderStatus } from '../api/client';
import ReminderBadge from '../components/ReminderBadge';

const STATUS_LABELS = {
  pending_transcription: 'Pending Transcription',
  transcribed: 'Transcribed',
  reminder_set: 'Reminder Set',
  failed: 'Transcription Failed',
};

export default function NoteDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [note, setNote] = useState(null);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);

  // Reminder form
  const [showReminderForm, setShowReminderForm] = useState(false);
  const [reminderMessage, setReminderMessage] = useState('');
  const [reminderTime, setReminderTime] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadNote = useCallback(async () => {
    try {
      const data = await fetchNote(id);
      setNote(data.note);
    } catch (err) {
      console.error('Failed to load note:', err);
      showToast('Note not found', 'error');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadNote();
  }, [loadNote]);

  // Poll for updates if note is processing
  useEffect(() => {
    let intervalId;
    if (note && note.status === 'pending_transcription') {
      intervalId = setInterval(() => {
        loadNote();
      }, 3000); // Poll every 3 seconds
    }
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [note?.status, loadNote]);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const handleCreateReminder = async (e) => {
    e.preventDefault();
    if (!reminderMessage.trim() || !reminderTime) return;

    setSubmitting(true);
    try {
      await createReminder(id, new Date(reminderTime).toISOString(), reminderMessage.trim());
      showToast('Reminder created!');
      setShowReminderForm(false);
      setReminderMessage('');
      setReminderTime('');
      await loadNote();
    } catch (err) {
      const errorMsg = err.response?.data?.error || 'Failed to create reminder';
      showToast(errorMsg, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteNote = async () => {
    if (!confirm('Delete this note and all its reminders?')) return;
    try {
      await deleteNote(id);
      showToast('Note deleted');
      navigate('/');
    } catch (err) {
      showToast('Failed to delete note', 'error');
    }
  };

  const handleDeleteReminder = async (reminderId) => {
    try {
      await deleteReminder(reminderId);
      showToast('Reminder cancelled');
      await loadNote();
    } catch (err) {
      showToast('Failed to cancel reminder', 'error');
    }
  };

  const handleToggleReminder = async (reminderId) => {
    try {
      await toggleReminderStatus(reminderId);
      await loadNote();
    } catch (err) {
      showToast('Failed to update status', 'error');
    }
  };

  if (loading) {
    return (
      <div className="loading-spinner">
        <div className="spinner" />
      </div>
    );
  }

  if (!note) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">
           <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        </div>
        <div className="empty-state-title">Note not found</div>
        <button className="back-btn" onClick={() => navigate('/')}>← Back to notes</button>
      </div>
    );
  }

  const statusKey = note.status?.replace('pending_transcription', 'pending');

  // Get min datetime for reminder input (now + 1 minute)
  const minDatetime = new Date(Date.now() + 60000).toISOString().slice(0, 16);

  return (
    <>
      <button className="back-btn" onClick={() => navigate('/')} id="back-button">
        ← Back to notes
      </button>

      {/* Header */}
      <div className="detail-header">
        <h1 className="detail-title">{note.title || `Voice Note #${note.id}`}</h1>
        <div className="detail-meta">
          <span className={`status-badge ${statusKey}`}>
            <span className="status-dot" />
            {STATUS_LABELS[note.status] || note.status}
          </span>
          <span>{new Date(note.created_at).toLocaleString()}</span>
        </div>
      </div>

      {/* Audio Player */}
      <div className="detail-section">
        <h2 className="detail-section-title">Audio</h2>
        <div className="glass-card" style={{ cursor: 'default' }}>
          {note.audio_filename ? (
            <audio
              className="audio-player"
              controls
              src={`${import.meta.env.VITE_API_URL || 'http://localhost:5001'}/notes/audio/${note.audio_filename}`}
              id="audio-player"
            >
              Your browser does not support audio playback.
            </audio>
          ) : (
            <p style={{ color: 'var(--text-muted)' }}>Audio file not available</p>
          )}
        </div>
      </div>

      {/* Transcript */}
      <div className="detail-section">
        <h2 className="detail-section-title">Transcript</h2>
        {note.transcript ? (
          <div className="transcript-box">{note.transcript}</div>
        ) : (
          <div className="glass-card" style={{ cursor: 'default', color: 'var(--text-muted)' }}>
            {note.status === 'pending_transcription'
              ? 'Transcription in progress...'
              : note.status === 'failed'
              ? 'Transcription failed. The audio may be in an unsupported format.'
              : 'No transcript available.'}
          </div>
        )}
      </div>

      {/* Reminders */}
      <div className="detail-section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-md)' }}>
          <h2 className="detail-section-title" style={{ marginBottom: 0 }}>Reminders</h2>
          <button
            className="btn btn-primary btn-sm"
            onClick={() => setShowReminderForm(!showReminderForm)}
            id="add-reminder-btn"
          >
            {showReminderForm ? '✕ Cancel' : '+ Add Reminder'}
          </button>
        </div>

        {/* Reminder Form */}
        {showReminderForm && (
          <div className="glass-card" style={{ cursor: 'default', marginBottom: 'var(--spacing-md)' }}>
            <form onSubmit={handleCreateReminder}>
              <div className="form-group">
                <label className="form-label">Reminder Message</label>
                <input
                  className="form-input"
                  type="text"
                  placeholder="What should I remind you about?"
                  value={reminderMessage}
                  onChange={(e) => setReminderMessage(e.target.value)}
                  required
                  maxLength={500}
                  id="reminder-message-input"
                />
              </div>
              <div className="form-group">
                <label className="form-label">When</label>
                <input
                  className="form-input"
                  type="datetime-local"
                  value={reminderTime}
                  onChange={(e) => setReminderTime(e.target.value)}
                  min={minDatetime}
                  required
                  id="reminder-time-input"
                />
              </div>
              <button
                className="btn btn-primary"
                type="submit"
                disabled={submitting}
                id="create-reminder-btn"
              >
                {submitting ? 'Creating...' : 'Create Reminder'}
              </button>
            </form>
          </div>
        )}

        {/* Reminder List */}
        {note.reminders?.length > 0 ? (
          <div className="glass-card" style={{ cursor: 'default' }}>
            {note.reminders.map((r) => (
              <div className="reminder-item" key={r.id}>
                <div className="reminder-info">
                  <div className="reminder-message">{r.message}</div>
                  <div className="reminder-datetime">
                    {new Date(r.remind_at).toLocaleString()}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ReminderBadge reminder={r} />
                  <button 
                    className="btn btn-primary btn-sm" 
                    onClick={() => handleToggleReminder(r.id)}
                  >
                    {r.is_triggered ? 'Undo' : 'Done'}
                  </button>
                  {!r.is_triggered && (
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={() => handleDeleteReminder(r.id)}
                      title="Cancel reminder"
                    >
                      ✕
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          !showReminderForm && (
            <div className="glass-card" style={{ cursor: 'default', textAlign: 'center', color: 'var(--text-muted)' }}>
              No reminders set for this note
            </div>
          )
        )}
      </div>

      {/* Actions */}
      <div style={{ marginTop: 'var(--spacing-xl)', textAlign: 'center' }}>
        <button className="btn btn-danger" onClick={handleDeleteNote} id="delete-note-btn">
          Delete Note
        </button>
      </div>

      {/* Toast */}
      {toast && (
        <div className={`toast ${toast.type}`}>{toast.message}</div>
      )}
    </>
  );
}
