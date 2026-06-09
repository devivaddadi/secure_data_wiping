#!/bin/bash
cd "$(dirname "$0")"
echo "Starting Secure Data Wiping System..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Checking dependencies..."
pip install -r requirements.txt -q

# Run application
echo "Launching Secure Data Wiping Protocol..."
python3 app.py

# Cleanup after application closes
echo "Cleaning up virtual environment to prevent dependency conflicts..."
deactivate 2>/dev/null || true
rm -rf venv
echo "Cleanup complete. Exiting."