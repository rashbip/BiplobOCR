#!/bin/bash
# Linux Launcher for BiplobOCR

# Ensure we are in the script's directory
cd "$(dirname "$0")"

# Check for virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the application
python3 src/main.py
