#!/bin/bash

# Kill any existing servers on ports 8000 and 8501
echo "Cleaning up existing servers..."
pkill -f "uvicorn src.main:app"
pkill -f "streamlit run src/app.py"
sleep 1

echo "Starting FastAPI Backend on port 8000..."
nohup .venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
echo "FastAPI backend started in background (logs: backend.log)."

echo "Starting Streamlit Frontend on port 8501..."
nohup .venv/bin/streamlit run src/app.py --server.port 8501 --server.address 0.0.0.0 > frontend.log 2>&1 &
echo "Streamlit frontend started in background (logs: frontend.log)."

sleep 2
echo "Done! Check server statuses using 'lsof -i :8000' and 'lsof -i :8501'."
