/**
 * API client for VoiceNote backend.
 */
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5001';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

// ── Notes ──────────────────────────────────────────

export const uploadVoiceNote = async (audioBlob, filename = 'recording.webm') => {
  const formData = new FormData();
  formData.append('audio', audioBlob, filename);
  const { data } = await api.post('/notes/voice', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const fetchNotes = async (page = 1, perPage = 20) => {
  const { data } = await api.get('/notes', { params: { page, per_page: perPage } });
  return data;
};

export const fetchNote = async (noteId) => {
  const { data } = await api.get(`/notes/${noteId}`);
  return data;
};

export const deleteNote = async (noteId) => {
  const { data } = await api.delete(`/notes/${noteId}`);
  return data;
};

// ── Reminders ──────────────────────────────────────

export const createReminder = async (noteId, remindAt, message) => {
  const { data } = await api.post(`/notes/${noteId}/remind`, {
    remind_at: remindAt,
    message,
  });
  return data;
};

export const fetchReminders = async () => {
  const { data } = await api.get('/reminders');
  return data;
};

export const createStandaloneReminder = async (remindAt, message) => {
  const { data } = await api.post('/reminders', { remind_at: remindAt, message });
  return data;
};

export const toggleReminderStatus = async (reminderId) => {
  const { data } = await api.patch(`/reminders/${reminderId}/toggle`);
  return data;
};

export const deleteReminder = async (reminderId) => {
  const { data } = await api.delete(`/reminders/${reminderId}`);
  return data;
};

export default api;
