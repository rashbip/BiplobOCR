import sys
import os
import subprocess

# 1. Enforcement Logic
# BiplobOCR is designed to run using its bundled Windows Python to ensure 
# all dependencies (Tesseract, PDF libraries) are consistent.
def bootstrap():
    # Only enforce on Windows
    if os.name == 'nt' and "BIPLO_OCR_BOOTSTRAPPED" not in os.environ:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        bundled_py = os.path.join(base_dir, "src", "python", "windows", "python.exe")
        
        if not os.path.exists(bundled_py):
            print(f"CRITICAL ERROR: Bundled Python not found at {bundled_py}")
            print("Please ensure the project is complete before running.")
            sys.exit(1)

        current_exe = os.path.abspath(sys.executable).lower()
        target_exe = os.path.abspath(bundled_py).lower()
        
        if current_exe != target_exe:
            # Set a flag to prevent infinite loops
            env = os.environ.copy()
            env["BIPLO_OCR_BOOTSTRAPPED"] = "1"
            env["PYTHONPATH"] = base_dir + os.pathsep + env.get("PYTHONPATH", "")
            
            # Re-launch using the bundled Python
            try:
                # Use creationflags=0x08000000 (CREATE_NO_WINDOW) if we want silent boot, 
                # but for run.py we usually want to see errors.
                result = subprocess.run([bundled_py] + sys.argv, env=env)
                sys.exit(result.returncode)
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
