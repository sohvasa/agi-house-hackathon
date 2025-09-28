import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiService from '../services/api';
import './SimulationReplay.css';

// Profile images using SVG data URIs - handles both formats (with and without "Agent" suffix)
const AGENT_PROFILES = {
  // New format (without Agent suffix)
  Prosecutor: {
    name: 'Prosecutor',
    avatar: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMjAiIGN5PSIyMCIgcj0iMjAiIGZpbGw9IiM0QTkwRTIiLz4KPHBhdGggZD0iTTIwIDIyQzIzLjMxMzcgMjIgMjYgMTkuMzEzNyAyNiAxNkMyNiAxMi42ODYzIDIzLjMxMzcgMTAgMjAgMTBDMTYuNjg2MyAxMCAxNCAxMi42ODYzIDE0IDE2QzE0IDE5LjMxMzcgMTYuNjg2MyAyMiAyMCAyMloiIGZpbGw9IndoaXRlIi8+CjxwYXRoIGQ9Ik0yMCAyNEMxNC40NzcyIDI0IDEwIDI4LjQ3NzIgMTAgMzRWMzZIMzBWMzRDMzAgMjguNDc3MiAyNS41MjI4IDI0IDIwIDI0WiIgZmlsbD0id2hpdGUiLz4KPC9zdmc+',
    color: '#4A90E2'
  },
  Defense: {
    name: 'Defense',
    avatar: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMjAiIGN5PSIyMCIgcj0iMjAiIGZpbGw9IiM2Qzc1N0QiLz4KPHBhdGggZD0iTTIwIDIyQzIzLjMxMzcgMjIgMjYgMTkuMzEzNyAyNiAxNkMyNiAxMi42ODYzIDIzLjMxMzcgMTAgMjAgMTBDMTYuNjg2MyAxMCAxNCAxMi42ODYzIDE0IDE2QzE0IDE5LjMxMzcgMTYuNjg2MyAyMiAyMCAMjIiIGZpbGw9IndoaXRlIi8+CjxwYXRoIGQ9Ik0yMCAyNEMxNC40NzcyIDI0IDEwIDI4LjQ3NzIgMTAgMzRWMzZIMzBWMzRDMzAgMjguNDc3MiAyNS41MjI4IDI0IDIwIDI0WiIgZmlsbD0id2hpdGUiLz4KPC9zdmc+',
    color: '#6C757D'
  },
  Judge: {
    name: 'Judge',
    avatar: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMjAiIGN5PSIyMCIgcj0iMjAiIGZpbGw9IiMyOEE3NDUiLz4KPHBhdGggZD0iTTIwIDIyQzIzLjMxMzcgMjIgMjYgMTkuMzEzNyAyNiAxNkMyNiAxMi42ODYzIDIzLjMxMzcgMTAgMjAgMTBDMTYuNjg2MyAxMCAxNCAxMi42ODYzIDE0IDE2QzE0IDE5LjMxMzcgMTYuNjg2MyAyMiAyMCAyMloiIGZpbGw9IndoaXRlIi8+CjxwYXRoIGQ9Ik0yMCAyNEMxNC40NzcyIDI0IDEwIDI4LjQ3NzIgMTAgMzRWMzZIMzBWMzRDMzAgMjguNDc3MiAyNS41MjI4IDI0IDIwIDI0WiIgZmlsbD0id2hpdGUiLz4KPC9zdmc+',
    color: '#28A745'
  },
  // Legacy format (with Agent suffix)
  ProsecutorAgent: {
    name: 'Prosecutor',
    avatar: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMjAiIGN5PSIyMCIgcj0iMjAiIGZpbGw9IiM0QTkwRTIiLz4KPHBhdGggZD0iTTIwIDIyQzIzLjMxMzcgMjIgMjYgMTkuMzEzNyAyNiAxNkMyNiAxMi42ODYzIDIzLjMxMzcgMTAgMjAgMTBDMTYuNjg2MyAxMCAxNCAxMi42ODYzIDE0IDE2QzE0IDE5LjMxMzcgMTYuNjg2MyAyMiAyMCAyMloiIGZpbGw9IndoaXRlIi8+CjxwYXRoIGQ9Ik0yMCAyNEMxNC40NzcyIDI0IDEwIDI4LjQ3NzIgMTAgMzRWMzZIMzBWMzRDMzAgMjguNDc3MiAyNS41MjI4IDI0IDIwIDI0WiIgZmlsbD0id2hpdGUiLz4KPC9zdmc+',
    color: '#4A90E2'
  },
  DefenseAgent: {
    name: 'Defense',
    avatar: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMjAiIGN5PSIyMCIgcj0iMjAiIGZpbGw9IiM2Qzc1N0QiLz4KPHBhdGggZD0iTTIwIDIyQzIzLjMxMzcgMjIgMjYgMTkuMzEzNyAyNiAxNkMyNiAxMi42ODYzIDIzLjMxMzcgMTAgMjAgMTBDMTYuNjg2MyAxMCAxNCAxMi42ODYzIDE0IDE2QzE0IDE5LjMxMzcgMTYuNjg2MyAyMiAyMCAyMloiIGZpbGw9IndoaXRlIi8+CjxwYXRoIGQ9Ik0yMCAyNEMxNC40NzcyIDI0IDEwIDI4LjQ3NzIgMTAgMzRWMzZIMzBWMzRDMzAgMjguNDc3MiAyNS41MjI4IDI0IDIwIDI0WiIgZmlsbD0id2hpdGUiLz4KPC9zdmc+',
    color: '#6C757D'
  },
  JudgeAgent: {
    name: 'Judge',
    avatar: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMjAiIGN5PSIyMCIgcj0iMjAiIGZpbGw9IiMyOEE3NDUiLz4KPHBhdGggZD0iTTIwIDIyQzIzLjMxMzcgMjIgMjYgMTkuMzEzNyAyNiAxNkMyNiAxMi42ODYzIDIzLjMxMzcgMTAgMjAgMTBDMTYuNjg2MyAxMCAxNCAxMi42ODYzIDE0IDE2QzE0IDE5LjMxMzcgMTYuNjg2MyAyMiAyMCAyMloiIGZpbGw9IndoaXRlIi8+CjxwYXRoIGQ9Ik0yMCAyNEMxNC40NzcyIDI0IDEwIDI4LjQ3NzIgMTAgMzRWMzZIMzBWMzRDMzAgMjguNDc3MiAyNS41MjI4IDI0IDIwIDI0WiIgZmlsbD0id2hpdGUiLz4KPC9zdmc+',
    color: '#28A745'
  }
};

// Function to parse and format text with markdown-style formatting
function formatMessageText(text) {
  if (!text) return text;
  
  // Split text by ** markers for bold
  const parts = text.split(/\*\*/);
  
  return parts.map((part, index) => {
    // Odd indices are bold text (between ** markers)
    if (index % 2 === 1) {
      return <strong key={index} className="formatted-bold">{part}</strong>;
    }
    
    // Even indices are regular text
    // Further split by bullet points for better formatting
    const lines = part.split('\n');
    return lines.map((line, lineIndex) => {
      // Check if line starts with bullet point
      if (line.trim().startsWith('•') || line.trim().startsWith('-')) {
        const bulletContent = line.replace(/^\s*[•\-]\s*/, '');
        return (
          <div key={`${index}-${lineIndex}`} className="bullet-point">
            <span className="bullet-marker">•</span>
            <span className="bullet-content">{bulletContent}</span>
          </div>
        );
      }
      
      // Check if line is a section header (ends with :)
      if (line.trim().endsWith(':') && line.trim().length > 1) {
        return (
          <div key={`${index}-${lineIndex}`} className="section-header">
            {line}
          </div>
        );
      }
      
      // Regular line
      if (line.trim()) {
        return (
          <div key={`${index}-${lineIndex}`} className="text-line">
            {line}
          </div>
        );
      }
      
      // Empty line for spacing
      return <br key={`${index}-${lineIndex}`} />;
    });
  }).flat();
}

function SimulationReplay() {
  const { id } = useParams();
  const navigate = useNavigate();
  const chatEndRef = useRef(null);
  
  const [simulation, setSimulation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0);
  const [displayedMessages, setDisplayedMessages] = useState([]);
  const [currentText, setCurrentText] = useState('');
  const [replaySpeed, setReplaySpeed] = useState(30); // characters per second

  useEffect(() => {
    fetchSimulation();
  }, [id]);

  // Helper function to ensure messages are sorted by timestamp
  const sortMessagesByTimestamp = (messages) => {
    if (!messages || !Array.isArray(messages)) return messages;
    
    return [...messages].sort((a, b) => {
      const timeA = new Date(a.timestamp || 0).getTime();
      const timeB = new Date(b.timestamp || 0).getTime();
      return timeA - timeB;
    });
  };

  useEffect(() => {
    // Scroll to bottom when new messages are added
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [displayedMessages, currentText]);

  const fetchSimulation = async () => {
    try {
      setLoading(true);
      const data = await apiService.getSimulationDetail(id);
      
      // Sort messages by timestamp to ensure proper order
      if (data && data.messages) {
        data.messages = sortMessagesByTimestamp(data.messages);
        
        // Ensure no content is truncated and all fields are present
        data.messages = data.messages.map(msg => ({
          ...msg,
          content: msg.content || '',  // Ensure content is never undefined
          agent_name: msg.agent_name || 'Unknown',  // Ensure agent name is present
          timestamp: msg.timestamp || new Date().toISOString()  // Ensure timestamp exists
        }));
        
        console.log(`Loaded ${data.messages.length} messages for replay`);
      }
      
      setSimulation(data);
      
      // If auto-play is desired, start playing immediately
      // startReplay();
    } catch (err) {
      setError('Failed to load simulation');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const startReplay = () => {
    if (!simulation || !simulation.messages || simulation.messages.length === 0) return;
    
    setIsPlaying(true);
    setCurrentMessageIndex(0);
    setDisplayedMessages([]);
    setCurrentText('');
    
    playNextMessage(0, []);
  };

  const playNextMessage = (index, currentMessages) => {
    if (!simulation || index >= simulation.messages.length) {
      setIsPlaying(false);
      return;
    }

    const message = simulation.messages[index];
    const text = message.content;
    let charIndex = 0;

    // Add message shell immediately
    const newMessage = {
      ...message,
      content: '',
      isTyping: true
    };
    const updatedMessages = [...currentMessages, newMessage];
    setDisplayedMessages(updatedMessages);

    // Type out the message character by character
    const typeInterval = setInterval(() => {
      if (charIndex < text.length) {
        const currentChunk = text.substring(0, charIndex + Math.min(3, text.length - charIndex));
        setCurrentText(currentChunk);
        
        // Update the message content
        updatedMessages[updatedMessages.length - 1].content = currentChunk;
        setDisplayedMessages([...updatedMessages]);
        
        charIndex += 3; // Type 3 characters at a time for smoother effect
      } else {
        // Message complete
        clearInterval(typeInterval);
        updatedMessages[updatedMessages.length - 1].isTyping = false;
        updatedMessages[updatedMessages.length - 1].content = text;
        setDisplayedMessages([...updatedMessages]);
        setCurrentText('');
        
        // Wait a bit before next message
        setTimeout(() => {
          playNextMessage(index + 1, updatedMessages);
        }, 1000);
      }
    }, 1000 / replaySpeed);
  };

  const stopReplay = () => {
    setIsPlaying(false);
    // Show all messages immediately
    if (simulation && simulation.messages) {
      setDisplayedMessages(simulation.messages.map(msg => ({
        ...msg,
        isTyping: false
      })));
    }
  };

  const resetReplay = () => {
    setIsPlaying(false);
    setCurrentMessageIndex(0);
    setDisplayedMessages([]);
    setCurrentText('');
  };

  const getAgentProfile = (agentName) => {
    return AGENT_PROFILES[agentName] || {
      name: agentName,
      avatar: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMjAiIGN5PSIyMCIgcj0iMjAiIGZpbGw9IiNBREI1QkQiLz4KPHBhdGggZD0iTTIwIDIyQzIzLjMxMzcgMjIgMjYgMTkuMzEzNyAyNiAxNkMyNiAxMi42ODYzIDIzLjMxMzcgMTAgMjAgMTBDMTYuNjg2MyAxMCAxNCAxMi42ODYzIDE0IDE2QzE0IDE5LjMxMzcgMTYuNjg2MyAyMiAyMCAyMloiIGZpbGw9IndoaXRlIi8+CjxwYXRoIGQ9Ik0yMCAyNEMxNC40NzcyIDI0IDEwIDI4LjQ3NzIgMTAgMzRWMzZIMzBWMzRDMzAgMjguNDc3MiAyNS41MjI4IDI0IDIwIDI0WiIgZmlsbD0id2hpdGUiLz4KPC9zdmc+',
      color: '#ADB5BD'
    };
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-animation">
          <div className="loading-ring"></div>
          <div className="loading-ring"></div>
          <div className="loading-ring"></div>
        </div>
        <div className="loading-text">Loading Simulation</div>
        <div className="loading-dots">
          <div className="loading-dot"></div>
          <div className="loading-dot"></div>
          <div className="loading-dot"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-message">
        {error}
        <button onClick={() => navigate('/dashboard')} className="btn btn-secondary" style={{ marginLeft: '1rem' }}>
          Back to Dashboard
        </button>
      </div>
    );
  }

  if (!simulation) {
    return (
      <div className="error-message">
        Simulation not found
      </div>
    );
  }

  return (
    <div className="simulation-replay">
      <div className="replay-header">
        <div className="replay-info">
          <button onClick={() => navigate('/dashboard')} className="back-button">
            ← Back
          </button>
          <h2>{simulation.case_name}</h2>
        </div>
        
        <div className="replay-controls">
          <button
            className="btn btn-primary"
            onClick={startReplay}
            disabled={isPlaying}
          >
            Play Replay
          </button>
          <button
            className="btn btn-secondary"
            onClick={stopReplay}
            disabled={!isPlaying}
          >
            Stop
          </button>
          <button
            className="btn btn-secondary"
            onClick={resetReplay}
          >
            Reset
          </button>
          <div className="speed-control">
            <label>Speed:</label>
            <select
              value={replaySpeed}
              onChange={(e) => setReplaySpeed(Number(e.target.value))}
              disabled={isPlaying}
            >
              <option value="10">Slow</option>
              <option value="30">Normal</option>
              <option value="60">Fast</option>
              <option value="120">Very Fast</option>
            </select>
          </div>
        </div>
      </div>

      <div className="chat-container">
        <div className="chat-messages">
          {displayedMessages.length === 0 && !isPlaying && (
            <div className="chat-empty">
              Click "Play Replay" to watch the simulation unfold
            </div>
          )}
          
          {displayedMessages.map((message, index) => {
            const profile = getAgentProfile(message.agent_name);
            const isJudge = message.agent_name === 'JudgeAgent' || message.agent_name === 'Judge';
            
            return (
              <div
                key={index}
                className={`chat-message ${isJudge ? 'judge-message' : ''}`}
              >
                <img
                  src={profile.avatar}
                  alt={profile.name}
                  className="agent-avatar"
                />
                <div className="message-content">
                  <div className="message-header">
                    <span className="agent-name" style={{ color: profile.color }}>
                      {profile.name}
                    </span>
                    <span className="message-time">
                      {formatTimestamp(message.timestamp)}
                    </span>
                  </div>
                  <div className="message-text">
                    {message.isTyping ? (
                      <>
                        {message.content}
                        <span className="typing-cursor">|</span>
                      </>
                    ) : (
                      <div className="formatted-content">
                        {formatMessageText(message.content)}
                      </div>
                    )}
                  </div>
                  {message.metadata && (
                    <>
                      {message.metadata.verdict && (
                        <div className="verdict-info">
                          <span className="verdict-label">Verdict:</span>
                          <span className="verdict-value">{message.metadata.verdict}</span>
                          <span className="confidence-label">Confidence:</span>
                          <span className="confidence-value">
                            {(message.metadata.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      )}
                      {message.metadata.key_factors && message.metadata.key_factors.length > 0 && (
                        <div className="key-factors">
                          <div className="factors-label">Key Factors:</div>
                          <ul className="factors-list">
                            {message.metadata.key_factors.map((factor, i) => (
                              <li key={i}>{factor}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            );
          })}
          
          <div ref={chatEndRef} />
        </div>
      </div>
    </div>
  );
}

export default SimulationReplay;
