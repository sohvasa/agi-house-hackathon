#!/bin/bash

# Start Full Stack Legal Simulation Application
echo "========================================="
echo "Legal Simulation System - Starting Servers"
echo "========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -q flask flask-cors pymongo python-dotenv

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "WARNING: .env file not found!"
    echo "Please create a .env file with:"
    echo "  GEMINI_API_KEY=your_key"
    echo "  MONGODB_CONNECTION_STRING=your_connection_string"
    echo ""
fi

# Start Flask backend in background
echo "Starting Flask backend server..."
cd backend
python app.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "npm is not installed. Please install Node.js and npm."
    kill $BACKEND_PID
    exit 1
fi

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Start React frontend
echo "Starting React frontend server..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "========================================="
echo "Servers are starting..."
echo "========================================="
echo "Backend API: http://localhost:5000"
echo "Frontend UI: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo "========================================="

# Function to handle shutdown
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up trap for clean shutdown
trap cleanup INT TERM

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
