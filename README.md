# Concord AI

Concord AI is a multi-agent dispute simulator that transforms how legal and business conflicts are analyzed. Our browser agents conduct extensive legal research from online law databases, while our simulation agents act as prosecutor, defense, and judge and argue, negotiate, and deliberate cases in real time. Using Monte Carlo simulations to test alternative agent strategies, Concord AI delivers verdicts across dozens of outcomes. The result is decision support, risk forecasting, and a new way to stress-test disputes in minutes.

Uses Python, React, MongoDB, Browser Use, Perplexity, and Gemini.

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
