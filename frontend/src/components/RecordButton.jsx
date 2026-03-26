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
        <div className="record-btn-inner" />
      </button>

      {isRecording ? (
        <>
          <div className="record-timer">{formatTime(duration)}</div>
          <div className="record-label">Recording... Tap to stop</div>
        </>
      ) : (
        <div className="record-label">Tap to record a voice note</div>
      )}
    </div>
  );
}
