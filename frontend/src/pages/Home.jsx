/**
 * Home page — Note list with recording button and reminders overview.
 */
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import RecordButton from '../components/RecordButton';
import NoteCard from '../components/NoteCard';
import { fetchNotes, fetchReminders, uploadVoiceNote } from '../api/client';
import ReminderBadge from '../components/ReminderBadge';

export default function Home() {
  const navigate = useNavigate();
  const [notes, setNotes] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [toast, setToast] = useState(null);

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
      const errorMsg = err.response?.data?.error || 'Failed to upload voice note';
      showToast(errorMsg, 'error');
    } finally {
      setUploading(false);
    }
  };

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

      {/* Upcoming Reminders */}
      {reminders.length > 0 && (
        <div className="detail-section">
          <h2 className="detail-section-title">🔔 Upcoming Reminders</h2>
          <div className="glass-card" style={{ cursor: 'default' }}>
            {reminders.map((r) => (
              <div className="reminder-item" key={r.id}>
                <div className="reminder-info">
                  <div className="reminder-message">{r.message}</div>
                  <div className="reminder-datetime">
                    {new Date(r.remind_at).toLocaleString()}
                  </div>
                </div>
                <ReminderBadge reminder={r} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Notes List */}
      <div className="detail-section">
        <h2 className="detail-section-title">📝 Your Notes</h2>

        {loading ? (
          <div className="loading-spinner">
            <div className="spinner" />
          </div>
        ) : notes.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">🎙️</div>
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
