#!/bin/bash
# Build standalone Linux bundle using PyInstaller
# Current environment: WSL Ubuntu 20.04

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

# Use the bundled venv
VENV="$PROJECT_ROOT/src/python/linux/venv"

if [ ! -d "$VENV" ]; then
    echo "Error: Virtual environment not found at $VENV"
    exit 1
fi

source "$VENV/bin/activate"

echo "=== Installing/Updating PyInstaller in venv ==="
pip install --upgrade pyinstaller

echo "=== Cleaning previous builds ==="
rm -rf build/ dist/BiplobOCR_Linux_Bundle/

echo "=== Starting PyInstaller Build (This may take a several minutes) ==="
pyinstaller --clean biplobocr_linux.spec

echo ""
echo "=== Build Complete! ==="
echo "Bundle is located at: dist/BiplobOCR_Linux_Bundle/"
echo "To run: ./dist/BiplobOCR_Linux_Bundle/BiplobOCR"
