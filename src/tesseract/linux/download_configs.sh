#!/bin/bash
# Download Tesseract configuration files for Linux
# Working directory: src/tesseract/linux

set -e

WORKDIR="/mnt/d/Python/BiplobOCR/src/tesseract/linux/tessdata"
mkdir -p "$WORKDIR/configs"
mkdir -p "$WORKDIR/tessconfigs"

echo "=== Downloading Tesseract Configs ==="

# List of common configs
configs=("pdf" "txt" "hocr" "alto" "tsv" "lstmbox" "wordstrbox" "makebox" "digits" "quiet" "ambigs.train" "box.train" "unlv")

for cfg in "${configs[@]}"; do
    wget -q "https://github.com/tesseract-ocr/tesseract/raw/main/tessdata/configs/$cfg" -O "$WORKDIR/configs/$cfg" || echo "Failed to download config $cfg"
done

# List of common tessconfigs
tessconfigs=("batch" "batch.nochop" "matdemo" "msfunt" "segue")

for tcfg in "${tessconfigs[@]}"; do
    wget -q "https://github.com/tesseract-ocr/tesseract/raw/main/tessdata/tessconfigs/$tcfg" -O "$WORKDIR/tessconfigs/$tcfg" || echo "Failed to download tessconfig $tcfg"
done

echo "=== Done ==="
ls -la "$WORKDIR/configs/"
