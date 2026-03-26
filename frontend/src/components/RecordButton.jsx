/**
 * RecordButton — Mic recording UI with MediaRecorder API.
 */
import { useState, useRef, useCallback } from 'react';

export default function RecordButton({ onRecordingComplete, disabled }) {
  const [isRecording, setIsRecording] = useState(false);
  const [duration, setDuration] = useState(0);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
    const secs = (seconds % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4',
      });

      chunksRef.current = [];
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mediaRecorder.mimeType });
        const ext = mediaRecorder.mimeType.includes('webm') ? 'webm' : 'm4a';
        onRecordingComplete?.(blob, `recording.${ext}`);

        // Stop all tracks
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start(1000); // collect data every second
      setIsRecording(true);
      setDuration(0);

      timerRef.current = setInterval(() => {
        setDuration((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      console.error('Microphone access denied:', err);
      alert('Microphone access is required to record voice notes. Please allow access and try again.');
    }
  }, [onRecordingComplete]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      clearInterval(timerRef.current);
    }
  }, [isRecording]);

  const handleClick = () => {
    if (disabled) return;
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <div className="record-section">
      <button
        className={`record-btn ${isRecording ? 'recording' : ''}`}
        onClick={handleClick}
        disabled={disabled}
        aria-label={isRecording ? 'Stop recording' : 'Start recording'}
        id="record-button"
      >
        <span className="record-btn-inner">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"></path>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
            <line x1="12" y1="19" x2="12" y2="23"></line>
            <line x1="8" y1="23" x2="16" y2="23"></line>
          </svg>
        </span>
      </button>

      <div className="record-text-group">
        {isRecording ? (
          <>
            <div className="record-timer">{formatTime(duration)}</div>
            <div className="record-label" style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-sm)' }}>
              Recording... Tap to stop
            </div>
          </>
        ) : (
          <>
            <div className="record-label" style={{ fontSize: 'var(--font-size-lg)', color: 'var(--text-primary)' }}>
              Start Recording
            </div>
            <div className="record-label" style={{ color: 'var(--text-muted)' }}>
              Tap the microphone to capture your thoughts
            </div>
          </>
        )}
      </div>
    </div>
  );
}
