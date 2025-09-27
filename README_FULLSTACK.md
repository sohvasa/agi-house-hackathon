# Legal Simulation Full Stack Application

A complete web application for running and viewing AI-powered legal case simulations. Features a Flask backend API and React frontend with real-time simulation replay.

## Architecture

- **Backend**: Flask REST API with MongoDB integration
- **Frontend**: React SPA with modern, clean UI
- **Database**: MongoDB for persistent storage
- **AI Models**: Google Gemini for agent reasoning

## Features

### Backend API Endpoints
- `GET /api/simulations` - List all simulations with filtering
- `GET /api/simulation/<id>` - Get simulation details
- `POST /api/run-simulation` - Create and run new simulation
- `GET /api/monte-carlo/<id>` - Get Monte Carlo run details
- `GET /api/statistics` - Database statistics

### Frontend Features
- **Dashboard**: View all simulations with statistics
- **New Case Form**: Configure and run simulations
- **Simulation Replay**: Chat-style replay with typing animation
- **Clean UI**: Minimal design with blue accent colors

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 14+
- MongoDB (Atlas or local)
- API Keys:
  - Google Gemini API key
  - MongoDB connection string
  - Perplexity API key (optional)

### Backend Setup

1. **Install Python dependencies**:
```bash
cd backend
pip install -r requirements.txt
pip install -r ../requirements.txt
```

2. **Configure environment variables**:
Create `.env` file in project root:
```env
GEMINI_API_KEY=your_gemini_api_key
MONGODB_CONNECTION_STRING=mongodb+srv://...
PERPLEXITY_API_KEY=your_perplexity_key  # Optional
```

3. **Start Flask server**:
```bash
cd backend
python app.py
```

The backend will run on `http://localhost:5000`

### Frontend Setup

1. **Install Node dependencies**:
```bash
cd frontend
npm install
```

2. **Start React development server**:
```bash
npm start
```

The frontend will run on `http://localhost:3000`

## Usage

### Creating a New Simulation

1. Navigate to `http://localhost:3000`
2. Click "New Case" in the navigation
3. Fill in the case details:
   - Case description
   - Jurisdiction
   - Number of simulations (1 for single, more for Monte Carlo)
   - Agent strategies (Prosecutor, Defense, Judge)
   - Case factors (Evidence strength, NDA presence, etc.)
4. Click "Run Simulation"

### Viewing Simulation Replay

1. Go to Dashboard
2. Find your simulation in the list
3. Click "View Replay"
4. In the replay view:
   - Click "Play Replay" to watch the simulation unfold
   - Adjust speed (Slow/Normal/Fast/Very Fast)
   - Messages appear with typing animation
   - Agent profiles show with colored avatars
   - Judge's verdict appears highlighted

### UI Design

- **Color Scheme**:
  - Primary: Blue (#4A90E2)
  - Background: Light gray (#f8f9fa)
  - Cards: White with subtle shadows
  - Text: Dark gray (#212529)

- **Components**:
  - Clean card-based layout
  - No emojis or gradients
  - Minimal clutter
  - Clear typography (Inter font)

## Development

### Backend Development

The Flask backend (`backend/app.py`) handles:
- API routing
- MongoDB operations
- Simulation execution
- Data serialization

Key functions:
```python
@app.route('/api/run-simulation', methods=['POST'])
def run_simulation():
    # Runs simulation with provided parameters
    # Saves to MongoDB automatically
    # Returns simulation results
```

### Frontend Development

React components (`frontend/src/components/`):
- `Dashboard.js` - Main dashboard view
- `NewCase.js` - Simulation creation form
- `SimulationReplay.js` - Chat-style replay viewer
- `Navigation.js` - Top navigation bar

API service (`frontend/src/services/api.js`):
```javascript
const apiService = {
  getSimulations: async (params) => {...},
  runSimulation: async (data) => {...},
  getSimulationDetail: async (id) => {...}
};
```

## Production Deployment

### Backend Deployment

1. **Use production WSGI server**:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

2. **Set production environment variables**:
```bash
export FLASK_ENV=production
```

### Frontend Deployment

1. **Build for production**:
```bash
cd frontend
npm run build
```

2. **Serve static files**:
- Use nginx or Apache
- Deploy to services like Vercel, Netlify, or AWS S3

### Database Considerations

- Use MongoDB Atlas for production
- Set up proper indexes for performance
- Configure connection pooling
- Enable authentication and SSL

## API Documentation

### Run Simulation
```http
POST /api/run-simulation
Content-Type: application/json

{
  "case_description": "Trade secret dispute...",
  "jurisdiction": "Federal",
  "num_simulations": 1,
  "prosecutor_strategy": "moderate",
  "defense_strategy": "moderate",
  "judge_temperament": "balanced",
  "has_nda": true,
  "evidence_strength": "moderate"
}
```

Response:
```json
{
  "status": "success",
  "simulation_id": "507f1f77bcf86cd799439011",
  "winner": "plaintiff",
  "confidence": 0.75,
  "execution_time": 45.2
}
```

## Troubleshooting

### Backend Issues
- **MongoDB connection fails**: Check connection string and network access
- **Simulation fails**: Verify API keys are set correctly
- **CORS errors**: Ensure flask-cors is installed and configured

### Frontend Issues
- **API calls fail**: Check backend is running on port 5000
- **Blank page**: Check browser console for errors
- **Replay not working**: Verify simulation has messages

## Future Enhancements

- [ ] WebSocket support for real-time simulation updates
- [ ] Export simulation results as PDF
- [ ] Advanced filtering and search
- [ ] User authentication and sessions
- [ ] Batch simulation processing
- [ ] Analytics dashboard
- [ ] Mobile responsive improvements

## License

This is a demonstration/research project. Not for production legal use.
