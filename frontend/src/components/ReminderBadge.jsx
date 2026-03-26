/**
 * ReminderBadge — Shows reminder time with status indicator.
 */

function formatReminderTime(isoString) {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = date - now;

  if (diffMs < 0) {
    return 'Past due';
  }

  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 60) return `in ${diffMins}m`;
  if (diffHours < 24) return `in ${diffHours}h`;
  if (diffDays < 7) return `in ${diffDays}d`;

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

export default function ReminderBadge({ reminder }) {
  return (
    <span
      className={`reminder-badge ${reminder.is_triggered ? 'triggered' : ''}`}
      title={`${reminder.message} — ${new Date(reminder.remind_at).toLocaleString()}`}
      id={`reminder-badge-${reminder.id}`}
    >
      <span className="reminder-icon">
        {reminder.is_triggered ? (
           <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
        ) : (
           <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
        )}
      </span>
      <span className="reminder-time">
        {reminder.is_triggered ? 'Done' : formatReminderTime(reminder.remind_at)}
      </span>
    </span>
  );
}
