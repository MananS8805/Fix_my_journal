#!/bin/bash

# Start Manuscript Formatting Agent on macOS/Linux

echo "========================================="
echo "Manuscript Formatting Agent"
echo "========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from python.org"
    exit 1
fi

# Check if pip packages are installed
echo "Checking dependencies..."
pip3 show fastapi > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        exit 1
    fi
fi

echo ""
echo "Starting API Server..."
echo "========================================="
echo ""
echo "API Available at: http://localhost:8001"
echo ""
echo "Swagger Docs:     http://localhost:8001/docs"
echo "ReDoc:            http://localhost:8001/redoc"
echo ""
echo "Press CTRL+C to stop the server"
echo "========================================="
echo ""

cd backend
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
