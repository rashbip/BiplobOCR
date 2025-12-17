
import subprocess
import shutil
import os
import signal
import time

# Store active process for cancellation
ACTIVE_PROCESS = None

def cancel_ocr():
    global ACTIVE_PROCESS
    if ACTIVE_PROCESS:
        try:
            ACTIVE_PROCESS.terminate()
        except:
            pass
        ACTIVE_PROCESS = None

def detect_pdf_type(pdf_path):
    # Logic to detect if PDF is text-based or image-based
    return "image"

def run_ocr(input_path, output_path, password=None, force=False, options=None):
    global ACTIVE_PROCESS
    
    cmd = ["ocrmypdf", input_path, output_path]
    
    if force:
        cmd.append("--force-ocr")
    else:
        cmd.append("--skip-text")

    if options:
        if options.get("deskew"): cmd.append("--deskew")
        if options.get("clean"): cmd.append("--clean")
        if options.get("rotate"): cmd.append("--rotate-pages")
        
        opt_level = options.get("optimize", "0")
        if opt_level != "0":
            cmd.extend(["--optimize", opt_level])

    # Sidecar generation
    sidecar = output_path.replace(".pdf", ".txt")
    cmd.extend(["--sidecar", sidecar])

    # Startup info to hide console window on Windows
    startupinfo = None
    if os.name == 'nt': 
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    try:
        ACTIVE_PROCESS = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            startupinfo=startupinfo
        )
        stdout, stderr = ACTIVE_PROCESS.communicate()
        
        if ACTIVE_PROCESS.returncode != 0:
            if ACTIVE_PROCESS.returncode < 0: # Terminated
                raise Exception("Process Cancelled")
            raise subprocess.CalledProcessError(ACTIVE_PROCESS.returncode, cmd, output=stdout, stderr=stderr)
            
    except Exception as e:
        if "Process Cancelled" in str(e):
            raise e
        raise e
    finally:
        ACTIVE_PROCESS = None

    return sidecar

def run_tesseract_export(input_path, output_base, format="hocr"):
    subprocess.check_call(["tesseract", input_path, output_base, format])
