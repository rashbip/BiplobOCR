#!/bin/bash
cd /mnt/d/Python/BiplobOCR/src/python/linux
source venv/bin/activate

echo "=== Testing PyInstaller ==="
pyinstaller --version

echo ""
echo "=== Testing ocrmypdf CLI ==="
python -m ocrmypdf --version

echo ""
echo "=== Python Environment Summary ==="
python --version
echo "Packages installed:"
pip list | wc -l
echo "packages total"
