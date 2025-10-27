#!/bin/bash

echo "===================================="
echo "    WNS Vox BOT - Quick Start"
echo "===================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://python.org"
    exit 1
fi

echo "[1/4] Checking Python installation..."
python3 --version

echo "[2/4] Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

echo "[3/4] Activating virtual environment..."
source venv/bin/activate

echo "[4/4] Installing dependencies..."
pip install -r requirements.txt

echo
echo "===================================="
echo "   Setup Complete! Starting App..."
echo "===================================="
echo
echo "The app will open in your browser at:"
echo "http://localhost:8501"
echo
echo "Press Ctrl+C to stop the application"
echo

# Start the application
streamlit run app_production.py --server.port 8501