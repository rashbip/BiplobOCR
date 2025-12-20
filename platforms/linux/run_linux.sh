#!/bin/bash
# Linux Launcher for BiplobOCR

# Ensure we are in the script's directory
cd "$(dirname "$0")/../.."

# Check for virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the application through the root run.py to ensure correct sys.path and environment
python3 run.py
