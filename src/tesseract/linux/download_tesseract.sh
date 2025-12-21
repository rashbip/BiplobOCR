#!/bin/bash
# Download static Tesseract for Linux
# Working directory: src/tesseract/linux

set -e

WORKDIR="/mnt/d/Python/BiplobOCR/src/tesseract/linux"
cd "$WORKDIR"

echo "=== Downloading static Tesseract 5.5.1 for Linux x86_64 ==="
wget "https://github.com/DanielMYT/tesseract-static/releases/download/tesseract-5.5.1-rebuild/tesseract.x86_64" -O tesseract

echo ""
echo "=== Making executable ==="
chmod +x tesseract

echo ""
echo "=== Testing ==="
./tesseract --version

echo ""
echo "=== Creating tessdata directory ==="
mkdir -p tessdata

echo ""
echo "=== Downloading essential traineddata files ==="
# English
wget "https://github.com/tesseract-ocr/tessdata_best/raw/main/eng.traineddata" -O tessdata/eng.traineddata

# Bengali
wget "https://github.com/tesseract-ocr/tessdata_best/raw/main/ben.traineddata" -O tessdata/ben.traineddata

# OSD (Orientation and Script Detection)
wget "https://github.com/tesseract-ocr/tessdata_best/raw/main/osd.traineddata" -O tessdata/osd.traineddata

echo ""
echo "=== Final structure ==="
ls -la
ls -la tessdata/
du -sh .

echo ""
echo "=== Testing with TESSDATA_PREFIX ==="
export TESSDATA_PREFIX="$WORKDIR/tessdata"
./tesseract --list-langs

echo ""
echo "=== SUCCESS! ==="
