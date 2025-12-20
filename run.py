import sys
import os
import subprocess

# 1. Enforcement Logic
# BiplobOCR is designed to run using its bundled Windows Python.
def bootstrap():
    # Only enforce on Windows
    if os.name == 'nt' and "BIPLO_OCR_BOOTSTRAPPED" not in os.environ:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        python_dir = os.path.join(base_dir, "src", "python", "windows")
        bundled_pyw = os.path.join(python_dir, "pythonw.exe")
        bundled_py = os.path.join(python_dir, "python.exe")
        
        # 1. Check if we are already running from the bundled folder
        current_exe = os.path.abspath(sys.executable).lower()
        bundle_path_abs = os.path.abspath(python_dir).lower()
        
        if current_exe.startswith(bundle_path_abs):
            return # We are already in the right place!

        # 2. Not in bundle? Re-launch using bundled pythonw.exe (Silent)
        exe_to_use = bundled_pyw if os.path.exists(bundled_pyw) else bundled_py
        
        if not os.path.exists(exe_to_use):
            print(f"CRITICAL ERROR: Bundled Python not found at {python_dir}")
            sys.exit(1)

        # Set a flag to prevent infinite loops
        env = os.environ.copy()
        env["BIPLO_OCR_BOOTSTRAPPED"] = "1"
        env["PYTHONPATH"] = base_dir + os.pathsep + env.get("PYTHONPATH", "")
        
        try:
            # Re-launch and exit
            subprocess.Popen([exe_to_use] + sys.argv, env=env)
            sys.exit(0)
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to launch bundled Python: {e}")
            sys.exit(1)

if __name__ == "__main__":
    bootstrap()
    
    # Add the current directory to sys.path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    # Force UTF-8 for Windows consoles
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except: pass

    from src.core.platform_utils import setup_python_environment
    setup_python_environment()

    from src.main import main
    main()
