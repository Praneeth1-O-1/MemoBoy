/**
 * Home page — Note list with recording button and reminders overview.
 */
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import RecordButton from '../components/RecordButton';
import NoteCard from '../components/NoteCard';
import { fetchNotes, fetchReminders, uploadVoiceNote, createStandaloneReminder, toggleReminderStatus } from '../api/client';
import ReminderBadge from '../components/ReminderBadge';

export default function Home() {
  const navigate = useNavigate();
  const [notes, setNotes] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [toast, setToast] = useState(null);

  const [showStandaloneForm, setShowStandaloneForm] = useState(false);
  const [standaloneMsg, setStandaloneMsg] = useState('');
  const [standaloneTime, setStandaloneTime] = useState('');
  const [standaloneSubmitting, setStandaloneSubmitting] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [notesData, remindersData] = await Promise.all([
        fetchNotes(),
        fetchReminders(),
      ]);
      setNotes(notesData.notes || []);
      setReminders(remindersData.reminders || []);
    } catch (err) {
      console.error('Failed to load data:', err);
      showToast('Failed to load notes. Is the backend running?', 'error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Poll for updates if any note is processing
  useEffect(() => {
    let intervalId;
    const hasPending = notes.some(note => note.status === 'pending_transcription');
    
    if (hasPending) {
      intervalId = setInterval(() => {
        loadData();
      }, 3000); // Poll every 3 seconds
    }
    
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [notes, loadData]);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const handleRecordingComplete = async (audioBlob, filename) => {
    setUploading(true);
    try {
      const result = await uploadVoiceNote(audioBlob, filename);
      showToast('Voice note uploaded and processed!', 'success');
      await loadData(); // Refresh the list

      // Navigate to new note detail
      if (result.note?.id) {
        navigate(`/notes/${result.note.id}`);
      }
    } catch (err) {
      console.error('Upload failed:', err);
      showToast(errorMsg, 'error');
    } finally {
      setUploading(false);
    }
  };

  const handleCreateStandalone = async (e) => {
    e.preventDefault();
    if (!standaloneMsg.trim() || !standaloneTime) return;
    setStandaloneSubmitting(true);
    try {
      await createStandaloneReminder(new Date(standaloneTime).toISOString(), standaloneMsg.trim());
      showToast('Reminder created!');
      setShowStandaloneForm(false);
      setStandaloneMsg('');
      setStandaloneTime('');
      await loadData();
    } catch (err) {
      showToast(err.response?.data?.error || 'Failed to create reminder', 'error');
    } finally {
      setStandaloneSubmitting(false);
    }
  };

  const handleToggleReminder = async (id) => {
    try {
      await toggleReminderStatus(id);
      await loadData();
    } catch (err) {
      showToast('Failed to update status', 'error');
    }
  };

  const minDatetime = new Date(Date.now() + 60000).toISOString().slice(0, 16);

  return (
    <>
      {/* Upload overlay */}
      {uploading && (
        <div className="upload-overlay">
          <div className="spinner" style={{ width: 60, height: 60, borderWidth: 4 }} />
          <div className="upload-text">Processing your voice note...</div>
          <div className="upload-subtext">Transcribing audio & analyzing with AI</div>
        </div>
      )}

      {/* Record Button */}
      <RecordButton onRecordingComplete={handleRecordingComplete} disabled={uploading} />

      {/* Reminders Section */}
      <div className="detail-section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-md)' }}>
          <h2 className="detail-section-title" style={{ marginBottom: 0 }}>Reminders</h2>
          <button 
            className="btn btn-primary btn-sm" 
            onClick={() => setShowStandaloneForm(!showStandaloneForm)}
          >
            {showStandaloneForm ? '✕ Cancel' : '+ New Reminder'}
          </button>
        </div>

        {showStandaloneForm && (
          <div className="glass-card" style={{ marginBottom: 'var(--spacing-md)', cursor: 'default' }}>
            <form onSubmit={handleCreateStandalone}>
              <div className="form-group">
                <label className="form-label">Reminder Message</label>
                <input
                  className="form-input"
                  type="text"
                  placeholder="What should I remind you about?"
                  value={standaloneMsg}
                  onChange={(e) => setStandaloneMsg(e.target.value)}
                  required
                  maxLength={500}
                />
              </div>
              <div className="form-group">
                <label className="form-label">When</label>
                <input
                  className="form-input"
                  type="datetime-local"
                  value={standaloneTime}
                  onChange={(e) => setStandaloneTime(e.target.value)}
                  min={minDatetime}
                  required
                />
              </div>
              <button className="btn btn-primary" type="submit" disabled={standaloneSubmitting}>
                {standaloneSubmitting ? 'Creating...' : 'Create Reminder'}
              </button>
            </form>
          </div>
        )}

        {reminders.length > 0 ? (
          <div className="glass-card" style={{ cursor: 'default' }}>
            {reminders.map((r) => (
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
                </div>
              </div>
            ))}
          </div>
        ) : (
          !showStandaloneForm && (
            <div className="glass-card" style={{ cursor: 'default', textAlign: 'center', color: 'var(--text-muted)' }}>
              No upcoming reminders
            </div>
          )
        )}
      </div>

      {/* Notes List */}
      <div className="detail-section">
        <h2 className="detail-section-title">Your Notes</h2>

        {loading ? (
          <div className="loading-spinner">
            <div className="spinner" />
          </div>
        ) : notes.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>
            </div>
            <div className="empty-state-title">No voice notes yet</div>
            <div className="empty-state-text">
              Tap the record button above to create your first voice note
            </div>
          </div>
        ) : (
          notes.map((note) => (
            <NoteCard
              key={note.id}
              note={note}
              onClick={(id) => navigate(`/notes/${id}`)}
            />
          ))
        )}
      </div>

      {/* Toast */}
      {toast && (
        <div className={`toast ${toast.type}`}>{toast.message}</div>
      )}
    </>
  );
}
