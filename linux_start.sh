#!/bin/bash

# BiplobOCR Linux Launcher
# Configures environment for bundled dependencies

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE_DIR="$SCRIPT_DIR/src"

echo "Launching BiplobOCR..."

# 1. Setup Embedded Ghostscript
export GS_LIB="$BASE_DIR/ghostscript/linux/lib"
export PATH="$BASE_DIR/ghostscript/linux/bin:$PATH"

# 2. Setup Embedded Tesseract
export TESSDATA_PREFIX="$BASE_DIR/tesseract/linux/tessdata"
export PATH="$BASE_DIR/tesseract/linux:$PATH"

# 3. Setup Python (if bundled, otherwise use system)
# Check for bundled python
if [ -f "$BASE_DIR/python/linux/bin/python" ]; then
    echo "Using bundled Python..."
    PYTHON_EXE="$BASE_DIR/python/linux/bin/python"
    export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
else
    echo "Using system Python..."
    PYTHON_EXE="python3"
fi

# 4. Launch
exec "$PYTHON_EXE" "$SCRIPT_DIR/run.py" "$@"
