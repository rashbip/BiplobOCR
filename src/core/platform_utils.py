
import os
import sys
import logging
import subprocess
import signal

IS_WINDOWS = os.name == 'nt'
IS_LINUX = sys.platform.startswith('linux')
IS_MAC = sys.platform == 'darwin'

def to_linux_path(path):
    """Translates a Windows path to a Linux path if running on Linux (WSL)."""
    if not IS_LINUX or not path:
        return path
        
    # Translate D:\ to /mnt/d/
    if len(path) > 2 and path[1:3] == ":\\":
        drive = path[0].lower()
        suffix = path[3:].replace('\\', '/')
        linux_path = f"/mnt/{drive}/{suffix}"
        return linux_path
        
    return path

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
    elif IS_LINUX:
        # Check for venv python
        bundled_python = os.path.join(base_dir, "python", "linux", "venv", "bin", "python")
        if os.path.exists(bundled_python):
            return bundled_python
            
    return sys.executable

def setup_python_environment():
    """Configure environment for bundled Python (like adding site-packages)."""
    base_dir = get_base_dir()
    if IS_WINDOWS:
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
    elif IS_LINUX:
        # Linux site-packages support (bundled)
        python_dir = os.path.join(base_dir, "python", "linux")
        # Check standard venv path first, then literal site-packages
        site_packages = os.path.join(python_dir, "venv", "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages")
        if not os.path.exists(site_packages):
            site_packages = os.path.join(python_dir, "site-packages")
            
        if os.path.exists(site_packages):
            if site_packages not in sys.path:
                sys.path.append(site_packages)
            os.environ["PYTHONPATH"] = site_packages + os.pathsep + os.environ.get("PYTHONPATH", "")
            logging.info(f"Added bundled Linux site-packages to path: {site_packages}")


def setup_tesseract_environment():
    """Configure environment to use bundled Tesseract if available."""
    try:
        base_dir = get_base_dir()
        platform_dir = get_tesseract_dir_name()
        
        tess_bin = os.path.join(base_dir, "tesseract", platform_dir)
        tess_data = os.path.join(tess_bin, "tessdata")
        
        tess_exe_name = get_tesseract_executable_name()
        tess_exe = os.path.join(tess_bin, tess_exe_name)

        if os.path.exists(tess_exe):
            # Prepend to PATH
            os.environ["PATH"] = tess_bin + os.pathsep + os.environ["PATH"]
            logging.info(f"Using bundled Tesseract: {tess_exe}")
        else:
            logging.warning(f"Bundled Tesseract NOT found at: {tess_exe}. Utilizing system PATH.")

        # Set TESSDATA_PREFIX if bundled data exists
        if os.path.exists(tess_data):
            os.environ["TESSDATA_PREFIX"] = tess_data
            logging.info(f"Tessdata Prefix: {tess_data}")
        
    except Exception as e:
        logging.error(f"Failed to setup local Tesseract: {e}")

def setup_ghostscript_environment():
    """Configure environment to use bundled Ghostscript if available."""
    try:
        base_dir = get_base_dir()
        
        if IS_WINDOWS:
            gs_bin = os.path.join(base_dir, "ghostscript", "windows", "bin")
            gs_lib = os.path.join(base_dir, "ghostscript", "windows", "lib")
        elif IS_LINUX:
            gs_bin = os.path.join(base_dir, "ghostscript", "linux", "bin")
            gs_lib = os.path.join(base_dir, "ghostscript", "linux", "lib")
        else:
            return

        if not os.path.exists(gs_bin):
            logging.warning(f"Bundled Ghostscript not found at: {gs_bin}. Utilizing system PATH.")
            return

        # Prepend to PATH
        if gs_bin not in os.environ["PATH"]:
            os.environ["PATH"] = gs_bin + os.pathsep + os.environ["PATH"]
        
        # Ghostscript often needs the lib directory in GS_LIB environment variable
        if os.path.exists(gs_lib):
            os.environ["GS_LIB"] = gs_lib
            logging.info(f"Set GS_LIB: {gs_lib}")

        logging.info(f"Using bundled Ghostscript from: {gs_bin}")
        
    except Exception as e:
        logging.error(f"Failed to setup local Ghostscript: {e}")

def get_tessdata_dir():
    """Returns the path to the tessdata directory."""
    base_dir = get_base_dir()
    return os.path.join(base_dir, "tesseract", get_tesseract_dir_name(), "tessdata")

def setup_fonts():
    """Register custom fonts from assets folder. Returns font family name on success, None on failure."""
    try:
        base_dir = get_base_dir()
        font_path = os.path.join(base_dir, "assets", "AdorNoirrit.ttf")
        
        if not os.path.exists(font_path):
            return None

        if IS_WINDOWS:
            import ctypes
            # FR_PRIVATE = 0x10.
            res = ctypes.windll.gdi32.AddFontResourceExW(font_path, 0x10, 0)
            if res:
                logging.info(f"Successfully loaded custom font (Windows): {font_path}")
                return "Li Ador Noirrit"
        
        elif IS_LINUX:
            # On Linux, we copy the font to ~/.local/share/fonts and run fc-cache
            home_dir = os.path.expanduser("~")
            local_fonts_dir = os.path.join(home_dir, ".local", "share", "fonts")
            os.makedirs(local_fonts_dir, exist_ok=True)
            
            target_font_path = os.path.join(local_fonts_dir, "AdorNoirrit.ttf")
            import shutil
            shutil.copy2(font_path, target_font_path)
            
            # Refresh font cache
            try:
                subprocess.run(["fc-cache", "-f", local_fonts_dir], check=False, 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logging.info(f"Registered custom font for Linux: {target_font_path}")
                return "Li Ador Noirrit"
            except:
                pass
                
        return None
    except Exception as e:
        logging.error(f"Error loading custom fonts: {e}")
        return None

def sanitize_for_linux(text):
    """Removes or replaces emojis that cause X11 Render crashes on some Linux systems."""
    if not IS_LINUX or not text:
        return text
    
    # Comprehensive replacement for emojis used in the app that crash X11
    emojis = [
        "📜", "🏠", "➕", "📦", "🕒", "⚙️", "📂", "👁", "🗑", "✅", "🔴", "🟢", "⚠", "🟥", "◀", "▶", "🔒", "🔑", "🔍", "🖼", "📄", "❌", "🚫", "⚠️", "⛔"
    ]

    clean_text = str(text)
    for e in emojis:
        clean_text = clean_text.replace(e, "")
    
    return clean_text.strip()






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

def linux_file_dialog(title="Select File", initialdir=None, multiple=False, save=False, filetypes=None):
    """Uses zenity to show a native file dialog on Linux to avoid Tkinter render bugs."""
    if not IS_LINUX: return None
    
    cmd = ["zenity", "--file-selection", "--title", title]
    if initialdir:
        cmd.extend(["--filename", os.path.join(initialdir, "")])
    if multiple:
        cmd.append("--multiple")
        cmd.append("--separator=|")
    if save:
        cmd.append("--save")
        cmd.append("--confirm-overwrite")
    
    if filetypes:
        for ft in filetypes:
            if isinstance(ft, tuple) and len(ft) >= 2:
                name, ext = ft
                # Zenity filter format: --file-filter="Name | *.ext *.ext2"
                # Convert list of extensions to space separated if needed, but our filetypes are usually strings like "*.pdf"
                cmd.append(f'--file-filter={name} | {ext}')

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            out = result.stdout.strip()
            if multiple:
                return out.split("|")
            return out
    except Exception as e:
        logging.error(f"Zenity dialog error: {e}")
    return None

def linux_directory_dialog(title="Select Folder", initialdir=None):
    """Uses zenity for native directory selection on Linux."""
    if not IS_LINUX: return None
    
    cmd = ["zenity", "--file-selection", "--directory", "--title", title]
    if initialdir:
        cmd.extend(["--filename", os.path.join(initialdir, "")])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        logging.error(f"Zenity directory dialog error: {e}")
    return None
