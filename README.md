# AGI House Hackathon

Multi-agent legal research system with Google Gemini integration.

## Setup

Install dependencies:
```bash
pip install -r requirements.txt
```

Create `.env` file:
```
GEMINI_API_KEY=your_key_here
PERPLEXITY_API_KEY=your_key_here  
BROWSER_USE_API_KEY=
MONGODB_CONNECTION_STRING=
```

## Backend

Install dependencies
Start the backend server:
```bash
python backend/app.py
```

Server runs on http://localhost:5000

## Frontend

Install and start frontend:
```bash
cd frontend
npm install
npm start
```

Frontend runs on http://localhost:3000


## Project Structure

```
agi-house-hackathon/
├── agents/           # Agent implementations
├── backend/          # Flask API server
├── frontend/         # React web interface
├── database/         # MongoDB integration
├── simulation/       # Monte Carlo simulations
├── util/             # Utility functions
└── examples/         # Usage examples
```

## Running Examples

```bash
python examples/agent_examples.py
python examples/statute_agent_demo.py
```

## Requirements

Python 3.12+
