import sys
import os

# Add the current directory to sys.path explicitly to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Force UTF-8 for stdout/stderr to fix UnicodeEncodeError in Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from src.core.platform_utils import setup_python_environment
setup_python_environment()

from src.main import main

if __name__ == "__main__":
    main()
