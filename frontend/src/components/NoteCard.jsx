/**
 * NoteCard — Displays a note with transcript excerpt and status.
 */
import ReminderBadge from './ReminderBadge';

const STATUS_LABELS = {
  pending_transcription: 'Pending',
  transcribed: 'Transcribed',
  reminder_set: 'Reminder Set',
  failed: 'Failed',
};

function formatDate(isoString) {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
  });
}

export default function NoteCard({ note, onClick }) {
  const statusKey = note.status?.replace('pending_transcription', 'pending');

  return (
    <div className="glass-card note-card" onClick={() => onClick?.(note.id)} id={`note-card-${note.id}`}>
      <div className="note-card-header">
        <h3 className="note-card-title">{note.title || `Voice Note #${note.id}`}</h3>
        <span className="note-card-time">{formatDate(note.created_at)}</span>
      </div>

      {note.transcript && (
        <p className="note-card-transcript">{note.transcript}</p>
      )}

      <div className="note-card-footer">
        <span className={`status-badge ${statusKey}`}>
          <span className="status-dot" />
          {STATUS_LABELS[note.status] || note.status}
        </span>

        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {note.reminders?.map((r) => (
            <ReminderBadge key={r.id} reminder={r} />
          ))}
        </div>
      </div>
    </div>
  );
}
