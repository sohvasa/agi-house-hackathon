import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';
import './NewCase.css';

function NewCase() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [actualVariables, setActualVariables] = useState(null);
  
  const [formData, setFormData] = useState({
    case_description: '',
    jurisdiction: 'Federal',
    num_simulations: 1,
    prosecutor_strategy: 'random',
    defense_strategy: 'random',
    judge_temperament: 'random',
    has_nda: true,
    evidence_strength: 'random',
    venue_bias: 'random'
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    
    if (!formData.case_description.trim()) {
      setError('Please provide a case description');
      return;
    }

    try {
      setLoading(true);
      const result = await apiService.runSimulation({
        ...formData,
        num_simulations: parseInt(formData.num_simulations)
      });
      
      setSuccess(true);
      
      // Store actual variables if they were randomized
      if (result.actual_variables) {
        setActualVariables(result.actual_variables);
      }
      
      // Redirect to the simulation detail page after a short delay
      setTimeout(() => {
        if (result.simulation_id) {
          navigate(`/simulation/${result.simulation_id}`);
        } else {
          navigate('/dashboard');
        }
      }, 3000); // Increased delay to show actual variables
      
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to run simulation');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="new-case">
      <div className="page-header">
        <h2>Create New Simulation</h2>
        <p className="page-subtitle">Configure and run a legal case simulation</p>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {success && (
        <div className="success-message">
          <div>Simulation started successfully!</div>
          {actualVariables && (
            <div style={{ marginTop: '10px', fontSize: '0.9em' }}>
              <strong>Using randomized values:</strong>
              <ul style={{ marginTop: '5px', marginBottom: 0, paddingLeft: '20px', textAlign: 'left' }}>
                {formData.prosecutor_strategy === 'random' && (
                  <li>Prosecutor: {actualVariables.prosecutor_strategy}</li>
                )}
                {formData.defense_strategy === 'random' && (
                  <li>Defense: {actualVariables.defense_strategy}</li>
                )}
                {formData.judge_temperament === 'random' && (
                  <li>Judge: {actualVariables.judge_temperament}</li>
                )}
                {formData.evidence_strength === 'random' && (
                  <li>Evidence: {actualVariables.evidence_strength}</li>
                )}
                {formData.venue_bias === 'random' && (
                  <li>Venue: {actualVariables.venue_bias}</li>
                )}
              </ul>
            </div>
          )}
          <div style={{ marginTop: '10px' }}>Redirecting...</div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="simulation-form">
        <div className="form-section">
          <h3>Case Information</h3>
          
          <div className="form-group">
            <label htmlFor="case_description" className="form-label">
              Case Description *
            </label>
            <textarea
              id="case_description"
              name="case_description"
              className="form-control"
              value={formData.case_description}
              onChange={handleChange}
              placeholder="Describe the legal case, including parties involved, allegations, evidence, and key facts..."
              rows={6}
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="jurisdiction" className="form-label">
                Jurisdiction
              </label>
              <select
                id="jurisdiction"
                name="jurisdiction"
                className="form-control form-select"
                value={formData.jurisdiction}
                onChange={handleChange}
              >
                <option value="Federal">Federal</option>
                <option value="State">State</option>
                <option value="California">California</option>
                <option value="New York">New York</option>
                <option value="Texas">Texas</option>
                <option value="Delaware">Delaware</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="num_simulations" className="form-label">
                Number of Simulations
              </label>
              <select
                id="num_simulations"
                name="num_simulations"
                className="form-control form-select"
                value={formData.num_simulations}
                onChange={handleChange}
              >
                <option value="1">1 (Single Trial)</option>
                <option value="3">3 (Small Monte Carlo)</option>
                <option value="5">5 (Medium Monte Carlo)</option>
                <option value="10">10 (Full Monte Carlo)</option>
              </select>
            </div>
          </div>
        </div>

        <div className="form-section">
          <h3>Agent Strategies</h3>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="prosecutor_strategy" className="form-label">
                Prosecutor Strategy
              </label>
              <select
                id="prosecutor_strategy"
                name="prosecutor_strategy"
                className="form-control form-select"
                value={formData.prosecutor_strategy}
                onChange={handleChange}
              >
                <option value="random">Random</option>
                <option value="aggressive">Aggressive</option>
                <option value="moderate">Moderate</option>
                <option value="conservative">Conservative</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="defense_strategy" className="form-label">
                Defense Strategy
              </label>
              <select
                id="defense_strategy"
                name="defense_strategy"
                className="form-control form-select"
                value={formData.defense_strategy}
                onChange={handleChange}
              >
                <option value="random">Random</option>
                <option value="aggressive">Aggressive</option>
                <option value="moderate">Moderate</option>
                <option value="conservative">Conservative</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="judge_temperament" className="form-label">
                Judge Temperament
              </label>
              <select
                id="judge_temperament"
                name="judge_temperament"
                className="form-control form-select"
                value={formData.judge_temperament}
                onChange={handleChange}
              >
                <option value="random">Random</option>
                <option value="strict">Strict</option>
                <option value="balanced">Balanced</option>
                <option value="lenient">Lenient</option>
              </select>
            </div>
          </div>
        </div>

        <div className="form-section">
          <h3>Case Factors</h3>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="evidence_strength" className="form-label">
                Evidence Strength
              </label>
              <select
                id="evidence_strength"
                name="evidence_strength"
                className="form-control form-select"
                value={formData.evidence_strength}
                onChange={handleChange}
              >
                <option value="random">Random</option>
                <option value="weak">Weak</option>
                <option value="moderate">Moderate</option>
                <option value="strong">Strong</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="venue_bias" className="form-label">
                Venue Bias
              </label>
              <select
                id="venue_bias"
                name="venue_bias"
                className="form-control form-select"
                value={formData.venue_bias}
                onChange={handleChange}
              >
                <option value="random">Random</option>
                <option value="plaintiff-friendly">Plaintiff-Friendly</option>
                <option value="neutral">Neutral</option>
                <option value="defendant-friendly">Defendant-Friendly</option>
              </select>
            </div>

            <div className="form-group">
              <div className="checkbox-group">
                <input
                  type="checkbox"
                  id="has_nda"
                  name="has_nda"
                  checked={formData.has_nda}
                  onChange={handleChange}
                />
                <label htmlFor="has_nda" className="checkbox-label">
                  NDA/Confidentiality Agreement Present
                </label>
              </div>
            </div>
          </div>
        </div>

        <div className="form-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => navigate('/dashboard')}
            disabled={loading}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Running Simulation...
              </>
            ) : (
              'Run Simulation'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

export default NewCase;
