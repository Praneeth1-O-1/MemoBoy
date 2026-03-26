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
      <span className="reminder-icon">{reminder.is_triggered ? '✅' : '🔔'}</span>
      <span className="reminder-time">
        {reminder.is_triggered ? 'Done' : formatReminderTime(reminder.remind_at)}
      </span>
    </span>
  );
}
