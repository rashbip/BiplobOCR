#!/bin/bash
cd /mnt/d/Python/BiplobOCR/src/python/linux
source venv/bin/activate
python -c "import ocrmypdf; import pikepdf; import fitz; print('All core imports OK!')"
