/**
 * App — Root component with routing.
 */
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import Home from './pages/Home';
import NoteDetail from './pages/NoteDetail';
import './index.css';

export default function App() {
  return (
    <Router>
      <div className="app-container">
        {/* Header */}
        <header className="app-header">
          <h1 className="app-logo">VoiceNote</h1>
          <p className="app-tagline">AI-Powered Voice Notes & Reminders</p>
        </header>

        {/* Navigation */}
        <nav className="nav-bar">
          <NavLink
            to="/"
            end
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            id="nav-home"
          >
            📝 Notes
          </NavLink>
        </nav>

        {/* Routes */}
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/notes/:id" element={<NoteDetail />} />
        </Routes>

        {/* Footer */}
        <footer style={{
          textAlign: 'center',
          padding: '32px 0',
          color: 'var(--text-muted)',
          fontSize: 'var(--font-size-xs)',
          borderTop: '1px solid var(--border-color)',
          marginTop: '48px'
        }}>
          VoiceNote — Built with Flask, React, OpenAI Whisper & GPT-4o
        </footer>
      </div>
    </Router>
  );
}
