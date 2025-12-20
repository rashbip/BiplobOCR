
import os
import sys
import logging
import subprocess
import signal

# Platform constants
IS_WINDOWS = os.name == 'nt'
IS_LINUX = sys.platform.startswith('linux')
IS_MAC = sys.platform == 'darwin'

def get_base_dir():
    """Returns the base directory of the project (src items)."""
    # Assuming this file is in src/core/platform_utils.py
    # src/core -> src
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_tesseract_dir_name():
    """Returns the platform-specific directory name for tesseract."""
    if IS_WINDOWS:
        return "windows"
    elif IS_LINUX:
        return "linux"
    elif IS_MAC:
        return "macos"
    else:
        return "unknown"

def get_tesseract_executable_name():
    """Returns the platform-specific executable name."""
    return "tesseract.exe" if IS_WINDOWS else "tesseract"

def get_python_executable():
    """Returns the path to the bundled Python executable if it exists, otherwise sys.executable."""
    base_dir = get_base_dir()
    if IS_WINDOWS:
        bundled_python = os.path.join(base_dir, "python", "windows", "python.exe")
        if os.path.exists(bundled_python):
            return bundled_python
    # For Linux/others, we will implement later as requested
    return sys.executable

def setup_python_environment():
    """Configure environment for bundled Python (like adding site-packages)."""
    if IS_WINDOWS:
        base_dir = get_base_dir()
        python_dir = os.path.join(base_dir, "python", "windows")
        site_packages = os.path.join(python_dir, "Lib", "site-packages")
        
        # Set TCL/TK libraries for the GUI to work in the bundle
        tcl_path = os.path.join(python_dir, "tcl", "tcl8.6")
        tk_path = os.path.join(python_dir, "tcl", "tk8.6")
        
        if os.path.exists(tcl_path):
            os.environ["TCL_LIBRARY"] = tcl_path
            logging.info(f"Set TCL_LIBRARY: {tcl_path}")
        if os.path.exists(tk_path):
            os.environ["TK_LIBRARY"] = tk_path
            logging.info(f"Set TK_LIBRARY: {tk_path}")
        
        if os.path.exists(site_packages):
            if site_packages not in sys.path:
                sys.path.append(site_packages)
            os.environ["PYTHONPATH"] = site_packages + os.pathsep + os.environ.get("PYTHONPATH", "")
            logging.info(f"Added bundled site-packages to path: {site_packages}")

def setup_tesseract_environment():
    """Configure environment to use bundled Tesseract if available."""
    try:
        base_dir = get_base_dir()
        platform_dir = get_tesseract_dir_name()
        
        tess_bin = os.path.join(base_dir, "tesseract", platform_dir)
        tess_data = os.path.join(tess_bin, "tessdata")
        
        tess_exe_name = get_tesseract_executable_name()
        tess_exe = os.path.join(tess_bin, tess_exe_name)

        if not os.path.exists(tess_exe):
            logging.warning(f"Bundled Tesseract not found at: {tess_exe}. Utilizing system PATH.")
            # On Linux, we might purely rely on system PATH, so this is fine.
            return

        # Prepend to PATH
        os.environ["PATH"] = tess_bin + os.pathsep + os.environ["PATH"]
        
        # Set TESSDATA_PREFIX
        # Only set if it exists or if we want to force it. 
        # Usually good to force if we are using bundled tesseract.
        if os.path.exists(tess_data):
            os.environ["TESSDATA_PREFIX"] = tess_data
            logging.info(f"Tessdata Prefix: {tess_data}")
        
        logging.info(f"Using bundled Tesseract: {tess_exe}")
        
    except Exception as e:
        logging.error(f"Failed to setup local Tesseract: {e}")

def get_tessdata_dir():
    """Returns the path to the tessdata directory."""
    base_dir = get_base_dir()
    return os.path.join(base_dir, "tesseract", get_tesseract_dir_name(), "tessdata")

def kill_process_tree(pid):
    """Terminates a process and its children in a platform-independent way."""
    try:
        logging.info(f"Terminating process: {pid}")
        if IS_WINDOWS:
            # Windows: /F (Force) /T (Tree) /PID
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            # Unix: Kill process group
            os.killpg(os.getpgid(pid), signal.SIGTERM)
    except Exception as e:
        logging.error(f"Error killing process: {e}")

def get_subprocess_startup_info():
    """Returns platform-specific startup info for subprocesses (hiding windows on Windows)."""
    if IS_WINDOWS:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        return startupinfo
    return None

def get_subprocess_creation_flags():
    """Returns platform-specific creation flags."""
    if IS_WINDOWS:
        # CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW (0x08000000)
        return subprocess.CREATE_NEW_PROCESS_GROUP | 0x08000000
    else:
        # On POSIX we handle start_new_session=True in Popen arguments usually,
        # but if we need a flag value, we can return 0
        return 0 
