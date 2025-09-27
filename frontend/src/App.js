import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import NewCase from './components/NewCase';
import SimulationReplay from './components/SimulationReplay';
import Navigation from './components/Navigation';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Navigation />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/new-case" element={<NewCase />} />
            <Route path="/simulation/:id" element={<SimulationReplay />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
