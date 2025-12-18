
import os
import tempfile

APP_NAME = "Biplob OCR"
# Use a dedicated subdir in system temp to avoid path issues and permission errors
TEMP_DIR = os.path.join(tempfile.gettempdir(), "BiplobOCR_Temp")

# Ensure it exists immediately to avoid race conditions or checks elsewhere failing
try:
    os.makedirs(TEMP_DIR, exist_ok=True)
except:
    pass
