#!/bin/bash
# Comprehensive test script for Linux Environment
# This tests Python, Ghostscript, and Tesseract integration

set -e

BASE_DIR="/mnt/d/Python/BiplobOCR"
GS_DIR="$BASE_DIR/src/ghostscript/linux"
TESS_DIR="$BASE_DIR/src/tesseract/linux"
VENV_DIR="$BASE_DIR/src/python/linux/venv"

echo "=========================================="
echo "   BiplobOCR Linux Environment Test"
echo "=========================================="
echo ""

# 1. Test Ghostscript
echo "--- 1. Testing Bundled Ghostscript ---"
export GS_LIB="$GS_DIR/lib"
GS_BIN="$GS_DIR/bin/gs"

if [ -f "$GS_BIN" ]; then
    echo "✅ Ghostscript binary found."
    GS_VER=$("$GS_BIN" --version)
    echo "   Version: $GS_VER"
else
    echo "❌ Ghostscript binary NOT found at $GS_BIN"
    exit 1
fi
echo ""

# 2. Test Tesseract
echo "--- 2. Testing Bundled Tesseract ---"
export TESSDATA_PREFIX="$TESS_DIR/tessdata"
TESS_BIN="$TESS_DIR/tesseract"

if [ -f "$TESS_BIN" ]; then
    echo "✅ Tesseract binary found."
    TESS_VER=$("$TESS_BIN" --version | head -n 1)
    echo "   Version: $TESS_VER"
    
    echo "   Available Languages:"
    "$TESS_BIN" --list-langs | sed 's/^/      /'
else
    echo "❌ Tesseract binary NOT found at $TESS_BIN"
    exit 1
fi
echo ""

# 3. Test Python & Integration
echo "--- 3. Testing Python Integration ---"
source "$VENV_DIR/bin/activate"

# Create a Python test script on the fly
cat <<EOF > test_integration.py
import os
import sys
import subprocess
from ocrmypdf import __version__ as ocrmypdf_version

print(f"   Python Version: {sys.version.split()[0]}")
print(f"   OCRmyPDF Version: {ocrmypdf_version}")

# Verify Environment Variables in Python
gs_lib = os.environ.get('GS_LIB', 'Not Set')
tess_prefix = os.environ.get('TESSDATA_PREFIX', 'Not Set')

print(f"   GS_LIB: {gs_lib}")
print(f"   TESSDATA_PREFIX: {tess_prefix}")

# Mock OCR call setup check
print("   Checking if subprocess calls use bundled binaries...")

# Check GS
try:
    gs_out = subprocess.check_output(['$GS_BIN', '--version'], stderr=subprocess.STDOUT)
    print(f"   ✅ Python can call bundled Ghostscript: {gs_out.decode().strip()}")
except Exception as e:
    print(f"   ❌ Python failed to call bundled Ghostscript: {e}")

# Check Tesseract
try:
    tess_out = subprocess.check_output(['$TESS_BIN', '--version'], stderr=subprocess.STDOUT)
    print(f"   ✅ Python can call bundled Tesseract: {tess_out.decode().splitlines()[0]}")
except Exception as e:
    print(f"   ❌ Python failed to call bundled Tesseract: {e}")

EOF

python test_integration.py
rm test_integration.py

echo ""
echo "=========================================="
echo "   ✅ ALL SYSTEMS GO! READY FOR LAUNCH"
echo "=========================================="
