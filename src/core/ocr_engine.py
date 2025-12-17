
import subprocess
import shutil
import os
import signal
import time
import re

# Store active process for cancellation
ACTIVE_PROCESS = None

def cancel_ocr():
    global ACTIVE_PROCESS
    if ACTIVE_PROCESS:
        try:
            pid = ACTIVE_PROCESS.pid
            if os.name == 'nt':
                # Force kill process tree (including Tesseract/Ghostscript)
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(pid)], 
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
        except:
            pass
        ACTIVE_PROCESS = None

def detect_pdf_type(pdf_path):
    return "image"

def run_ocr(input_path, output_path, password=None, force=False, options=None, progress_callback=None):
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
    
    # Add verbose logging to catch page numbers
    cmd.append("-v")
    
    # Custom Thread/Job Control
    # 1. Thread Limit (Internal Tesseract threads per page)
    # We keep this low (1) to prevent CPU hogging unless GPU is enabled (maybe allow 2?)
    env = os.environ.copy()
    env["OMP_THREAD_LIMIT"] = "1" 

    # 2. Job Limit (Parallel pages processed)
    # Controlled by user setting "Max CPU Threads"
    safe_jobs = 1
    if options:
        # User defined max threads
        user_max = options.get("max_cpu_threads", 2)
        safe_jobs = max(1, int(user_max))
        
        # If GPU is enabled, we might allow slightly more parallelism if we trust the GPU
        if options.get("use_gpu"):
            # Tesseract GPU support is tricky. If user enabled it, we assume they want speed.
            # But we still respect the limit to avoid freezing.
            pass
            
    cmd.extend(["--jobs", str(safe_jobs)])
    
    # GPU OpenCL override? 
    # Tesseract might auto-detect. We can't easily force specific device via CLI args 
    # without config vars, but we can set env vars if known.
    if options.get("gpu_device") and options.get("gpu_device") != "Auto":
        # Attempt to hint device (Experimental)
        # This part depends heavily on Tesseract build.
        pass

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
            startupinfo=startupinfo,
            bufsize=1,
            universal_newlines=True,
            env=env
        )
        
        # Read stderr line by line for progress
        while True:
            # Check explicit cancellation first
            if ACTIVE_PROCESS is None:
                raise Exception("Process Cancelled")

            line = ACTIVE_PROCESS.stderr.readline()
            if not line and ACTIVE_PROCESS.poll() is not None:
                break
            
            if line:
                # Try to parse page number
                match = re.search(r'(?:INFO\s+-\s+|Page\s+)(\d+)', line)
                if match and progress_callback:
                    try:
                        page_num = int(match.group(1))
                        progress_callback(page_num)
                    except:
                        pass
        
        # Final check
        if ACTIVE_PROCESS is None:
             raise Exception("Process Cancelled")

        return_code = ACTIVE_PROCESS.poll()
        
        if return_code != 0:
            # If we killed it, return_code might be 1 or 255 or -term
            # We assume if ACTIVE_PROCESS is None (cleared by cancel) it was cancelled
            if ACTIVE_PROCESS is None: 
                raise Exception("Process Cancelled")
            
            # Read any remaining stderr
            rem_stderr = ACTIVE_PROCESS.stderr.read()
            raise subprocess.CalledProcessError(return_code, cmd, output="", stderr=rem_stderr)
            
    except Exception as e:
        if "Process Cancelled" in str(e):
            raise e
        raise e
    finally:
        ACTIVE_PROCESS = None

    return sidecar

def run_tesseract_export(input_path, output_base, format="hocr"):
    subprocess.check_call(["tesseract", input_path, output_base, format])
