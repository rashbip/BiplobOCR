#!/bin/bash
# Linux Launcher for BiplobOCR - Prioritizes bundled environment

# Get project root (parent of parent of this script)
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

# Path to bundled venv
BUNDLED_VENV="$PROJECT_ROOT/src/python/linux/venv"

if [ -d "$BUNDLED_VENV" ]; then
    echo "Using bundled Python environment..."
    source "$BUNDLED_VENV/bin/activate"
else
    echo "Bundled environment not found. Falling back to system python..."
fi

# Run the application
python3 run.py
