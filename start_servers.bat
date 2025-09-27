@echo off
REM Start Full Stack Legal Simulation Application (Windows)

echo =========================================
echo Legal Simulation System - Starting Servers
echo =========================================

REM Check for .env file
if not exist .env (
    echo.
    echo WARNING: .env file not found!
    echo Please create a .env file with:
    echo   GEMINI_API_KEY=your_key
    echo   MONGODB_CONNECTION_STRING=your_connection_string
    echo.
)

REM Install Python dependencies
echo Installing Python dependencies...
pip install flask flask-cors pymongo python-dotenv

REM Start Flask backend
echo Starting Flask backend server...
start /B cmd /c "cd backend && python app.py"

REM Wait a moment for backend to start
timeout /t 3 /nobreak > nul

REM Check if npm is installed
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo npm is not installed. Please install Node.js and npm.
    exit /b 1
)

REM Install frontend dependencies if needed
if not exist frontend\node_modules (
    echo Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
)

REM Start React frontend
echo Starting React frontend server...
cd frontend
start cmd /k npm start
cd ..

echo.
echo =========================================
echo Servers are starting...
echo =========================================
echo Backend API: http://localhost:5000
echo Frontend UI: http://localhost:3000
echo.
echo Close this window to keep servers running
echo Or press Ctrl+C in each server window to stop
echo =========================================

pause
