
import os
import tempfile

APP_NAME = "Biplob OCR"

# Standardize pathing using platform_utils
from . import platform_utils
user_data_dir = platform_utils.get_app_data_dir()
TEMP_DIR = os.path.join(user_data_dir, "temp")

# Ensure it exists immediately
try:
    os.makedirs(TEMP_DIR, exist_ok=True)
except:
    pass
