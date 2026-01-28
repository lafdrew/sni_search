/**
 * App.tsx
 *
 * Main application with routing
 */

import { Routes, Route, Navigate } from 'react-router-dom';
import { HeroSection } from './sections/HeroSection';
import { ChatContainer } from './components/agent-trace/ChatContainer';

function App() {
  return (
    <Routes>
      {/* Landing page */}
      <Route path="/" element={<HeroSection />} />

      {/* Chat interface */}
      <Route path="/chat" element={<ChatContainer />} />

      {/* Redirect unknown routes to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
