#!/bin/bash
echo "🦁 Starting Hunter Agency Dashboard..."
echo "======================================"

if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🚀 Starting API server on http://localhost:8000"
echo "📖 API docs: http://localhost:8000/docs"
echo "Press Ctrl+C to stop"

python main.py
