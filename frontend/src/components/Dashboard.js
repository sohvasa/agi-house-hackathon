import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import apiService from '../services/api';
import './Dashboard.css';

function Dashboard() {
  const [simulations, setSimulations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statistics, setStatistics] = useState(null);

  useEffect(() => {
    fetchSimulations();
    fetchStatistics();
  }, []);

  const fetchSimulations = async () => {
    try {
      setLoading(true);
      const data = await apiService.getSimulations({ limit: 20 });
      setSimulations(data.simulations || []);
    } catch (err) {
      setError('Failed to load simulations');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const stats = await apiService.getStatistics();
      setStatistics(stats);
    } catch (err) {
      console.error('Failed to load statistics:', err);
    }
  };

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'completed':
        return 'badge badge-success';
      case 'in_progress':
        return 'badge badge-warning';
      case 'failed':
        return 'badge badge-danger';
      default:
        return 'badge badge-secondary';
    }
  };

  const getOutcomeBadgeClass = (outcome) => {
    if (outcome === 'plaintiff') return 'badge badge-primary';
    if (outcome === 'defendant') return 'badge badge-secondary';
    return 'badge badge-secondary';
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner spinner-lg"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-message">
        {error}
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>Simulation Dashboard</h2>
        <Link to="/new-case" className="btn btn-primary">
          Create New Simulation
        </Link>
      </div>

      {statistics && (
        <div className="statistics-row">
          <div className="stat-card">
            <div className="stat-value">{statistics.total_simulations || 0}</div>
            <div className="stat-label">Total Simulations</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{statistics.simulations_by_status?.completed || 0}</div>
            <div className="stat-label">Completed</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{statistics.simulations_by_status?.in_progress || 0}</div>
            <div className="stat-label">In Progress</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{statistics.total_research_entries || 0}</div>
            <div className="stat-label">Research Entries</div>
          </div>
        </div>
      )}

      <div className="simulations-section">
        <h3>Recent Simulations</h3>
        
        {simulations.length === 0 ? (
          <div className="empty-state">
            <p>No simulations found</p>
            <Link to="/new-case" className="btn btn-primary">
              Create Your First Simulation
            </Link>
          </div>
        ) : (
          <div className="simulations-grid">
            {simulations.map((sim) => (
              <div key={sim.id} className="simulation-card card">
                <div className="simulation-header">
                  <h4>{sim.case_name}</h4>
                  <span className={getStatusBadgeClass(sim.status)}>
                    {sim.status}
                  </span>
                </div>
                
                <div className="simulation-meta">
                  <div className="meta-item">
                    <span className="meta-label">Type:</span>
                    <span className="meta-value">{sim.simulation_type}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Messages:</span>
                    <span className="meta-value">{sim.message_count}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Created:</span>
                    <span className="meta-value">{formatDate(sim.created_at)}</span>
                  </div>
                </div>

                {sim.outcome && (
                  <div className="simulation-outcome">
                    <span className="outcome-label">Outcome:</span>
                    <span className={getOutcomeBadgeClass(sim.outcome)}>
                      {sim.outcome} wins
                    </span>
                  </div>
                )}

                {sim.summary && (
                  <div className="simulation-summary">
                    {sim.summary}
                  </div>
                )}

                <div className="simulation-actions">
                  <Link 
                    to={`/simulation/${sim.id}`} 
                    className="btn btn-sm btn-primary"
                  >
                    View Replay
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
