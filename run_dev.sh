#!/bin/bash

set -e

echo "=== Wine Photo Verification - Development Mode ==="

# Check if backend venv exists
if [ ! -d "./backend/.venv" ]; then
    echo "Creating backend virtual environment..."
    cd backend
    uv venv
    source .venv/bin/activate
    uv pip install -r requirements.txt
    cd ..
else
    echo "Backend venv exists"
fi

# Create data directories
mkdir -p data/cache data/images/original data/images/processed data/images/crops data/results

# Load environment variables
if [ -f .env ]; then
    echo "Loading environment from .env"
    set -a
    source .env
    set +a
fi

# Function to check if a port is in use
check_port() {
    lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1
}

# Function to kill process on a port
kill_port() {
    local port=$1
    local pids=$(lsof -Pi :$port -sTCP:LISTEN -t 2>/dev/null)
    if [ -n "$pids" ]; then
        echo "Killing process on port $port (PIDs: $pids)..."
        kill -9 $pids 2>/dev/null
        sleep 1
    fi
}

# Kill any existing backend process and start fresh
if check_port 8001; then
    kill_port 8001
fi

echo "Starting backend on port 8001..."
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8001 --host 127.0.0.1 &
BACKEND_PID=$!
cd ..
echo "Backend started with PID $BACKEND_PID"
sleep 3

# Kill any existing frontend process and start fresh
if check_port 3001; then
    kill_port 3001
fi

echo "Starting frontend on port 3001..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    pnpm install
fi
pnpm dev &
FRONTEND_PID=$!
cd ..
echo "Frontend started with PID $FRONTEND_PID"

echo ""
echo "=== Development servers running ==="
echo "Backend API: http://localhost:8001"
echo "Frontend: http://localhost:3001"
echo "API Docs: http://localhost:8001/docs"
echo ""
echo "Press Ctrl+C to stop"

# Wait for interrupt
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT
wait
