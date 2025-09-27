import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  withCredentials: false, // Set to true only if you need cookies/auth
});

// API Service
const apiService = {
  // Get list of simulations
  getSimulations: async (params = {}) => {
    try {
      const response = await api.get('/api/simulations', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching simulations:', error);
      throw error;
    }
  },

  // Get simulation details
  getSimulationDetail: async (simulationId) => {
    try {
      const response = await api.get(`/api/simulation/${simulationId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching simulation detail:', error);
      throw error;
    }
  },

  // Run new simulation
  runSimulation: async (data) => {
    try {
      const response = await api.post('/api/run-simulation', data);
      return response.data;
    } catch (error) {
      console.error('Error running simulation:', error);
      throw error;
    }
  },

  // Get Monte Carlo details
  getMonteCarloDetails: async (monteCarloId) => {
    try {
      const response = await api.get(`/api/monte-carlo/${monteCarloId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching Monte Carlo details:', error);
      throw error;
    }
  },

  // Get statistics
  getStatistics: async () => {
    try {
      const response = await api.get('/api/statistics');
      return response.data;
    } catch (error) {
      console.error('Error fetching statistics:', error);
      throw error;
    }
  },
};

export default apiService;
