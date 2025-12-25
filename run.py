import sys
import os
import subprocess

# 1. Enforcement Logic
# BiplobOCR is designed to run using its bundled Windows Python.
def bootstrap():
    # Only enforce on Windows/Linux if not already bootstrapped
    if "BIPLO_OCR_BOOTSTRAPPED" not in os.environ:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        if os.name == 'nt':
            python_dir = os.path.join(base_dir, "src", "python", "windows")
            bundled_pyw = os.path.join(python_dir, "pythonw.exe")
            bundled_py = os.path.join(python_dir, "python.exe")
            exe_to_use = bundled_pyw if os.path.exists(bundled_pyw) else bundled_py
        else:
            # Linux: Check for venv or bundled python
            python_bin_dir = os.path.join(base_dir, "src", "python", "linux", "venv", "bin")
            if not os.path.exists(python_bin_dir):
                python_bin_dir = os.path.join(base_dir, "src", "python", "linux", "bin")
            exe_to_use = os.path.join(python_bin_dir, "python")
        
        if not os.path.exists(exe_to_use):
            # If bundled not found, do not bootstrap, just continue with system
            return 

        # 1. Check if we are already running from the bundled folder
        current_exe = os.path.abspath(sys.executable).lower()
        bundle_exe_abs = os.path.abspath(exe_to_use).lower()
        
        if current_exe == bundle_exe_abs:
            return # We are already in the right place!

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
            # Fallback to system if bootstrap fails
            return


def setup_linux_bundle_env():
    """Setup Tcl/Tk paths for Linux PyInstaller bundle."""
    if sys.platform.startswith('linux') and hasattr(sys, '_MEIPASS'):
        bundle_dir = sys._MEIPASS
        tcl_dir = os.path.join(bundle_dir, 'tcl')
        tk_dir = os.path.join(bundle_dir, 'tk')
        
        if os.path.exists(tcl_dir):
            os.environ['TCL_LIBRARY'] = tcl_dir
        if os.path.exists(tk_dir):
            os.environ['TK_LIBRARY'] = tk_dir

if __name__ == "__main__":
    setup_linux_bundle_env()
    bootstrap()
    
    # Add the current directory to sys.path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    # Force UTF-8 for Windows consoles
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except: pass

    from src.core.platform_utils import setup_python_environment, setup_tesseract_environment, setup_ghostscript_environment, setup_fonts
    setup_python_environment()
    setup_tesseract_environment()
    setup_ghostscript_environment()
    # loaded_font = setup_fonts()
    loaded_font = None # Disable custom font to avoid X11 crash

    # If font failed to load, set fallbacks in the theme
    from src.core import theme
    if sys.platform.startswith('linux'):
        # On Linux, avoid custom fonts or 'Segoe UI' which trigger X11 BadLength
        # Use standard fonts that are likely to be found or handled gracefully
        theme.MAIN_FONT = "DejaVu Sans"
        theme.HEADER_FONT = "DejaVu Sans"
    elif not loaded_font:
        theme.MAIN_FONT = "Segoe UI"
        theme.HEADER_FONT = "Segoe UI"
    else:
        theme.MAIN_FONT = loaded_font
        theme.HEADER_FONT = loaded_font


    from src.main import main
    main()
