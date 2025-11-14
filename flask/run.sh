#!/bin/bash

# Quick run script for Flask Chat Application

echo "🚀 Starting Flask Chat Application..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run ./setup.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import flask" 2>/dev/null; then
    echo "❌ Dependencies not installed!"
    echo "Please run ./setup.sh first"
    exit 1
fi

echo "✓ Virtual environment activated"
echo "✓ Dependencies found"
echo ""
echo "Starting server on http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""

# Run the application
python app.py
