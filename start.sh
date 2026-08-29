#!/bin/bash

echo "Starting Dad of Anton applications..."

# Setup and start backend
echo "Setting up FastAPI backend..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt
PYTHONUNBUFFERED=1 uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Setup and start frontend
echo "Setting up Next.js frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi
npm run dev &
FRONTEND_PID=$!
cd ..

echo "Both applications started!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID