
import subprocess
import os
import signal
import re
import shutil
import tempfile
import sys
from .constants import APP_NAME, TEMP_DIR

# Store active process for cancellation
ACTIVE_PROCESS = None

def detect_pdf_type(file_path):
    """
    Check if PDF is text-based (Digital) or scanned images.
    Returns: 'text', 'image', or 'mixed'
    """
    try:
        # pip install pymupdf
        import fitz 
        doc = fitz.open(file_path)
        
        has_text = False
        has_images = False
        
        for page in doc:
            if page.get_text().strip():
                has_text = True
            if page.get_images():
                has_images = True
                
        doc.close()
        
        if has_text and not has_images: return 'text'
        if has_images and not has_text: return 'image'
        return 'mixed'
        
    except ImportError:
        return 'unknown' # Fallback if pymupdf missing
    except:
        return 'unknown'

def run_tesseract_export(pdf_path, output_txt):
    """
    Running tesseract directly just to extract text is complex for PDFs.
    Better used for Images. For PDFs, we rely on ocrmypdf sidecar.
    """
    pass

def cancel_ocr():
    global ACTIVE_PROCESS
    if ACTIVE_PROCESS:
        try:
            print(f"Terminating process: {ACTIVE_PROCESS.pid}")
            
            # Kill the entire process tree to ensure Tesseract/Ghostscript also die
            if os.name == 'nt':
                # Windows: /F (Force) /T (Tree) /PID
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(ACTIVE_PROCESS.pid)], 
                               creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                # Unix: Kill progress group
                os.killpg(os.getpgid(ACTIVE_PROCESS.pid), signal.SIGTERM)
                
            ACTIVE_PROCESS = None
        except Exception as e:
            print(f"Error killing process: {e}")

def run_ocr(input_path, output_path, password=None, force=False, options=None, progress_callback=None):
    """
    Executes OCRmyPDF on the input file.
    Retries on CPU if GPU fails.
    """
    global ACTIVE_PROCESS
    
    # 1. Prepare Base CMD
    base_cmd = ["ocrmypdf"]
    if force: base_cmd.append("--force-ocr")
    else: base_cmd.append("--skip-text")

    if options:
        if options.get("deskew"): base_cmd.append("--deskew")
        if options.get("clean"): base_cmd.append("--clean")
        if options.get("rotate"): base_cmd.append("--rotate-pages")
        if options.get("optimize", "0") != "0": 
            base_cmd.extend(["--optimize", options.get("optimize")])
        
        # Language
        lang = options.get("language", "eng")
        base_cmd.extend(["-l", lang])
            
    sidecar_file = output_path.replace(".pdf", ".txt")
    base_cmd.extend(["--sidecar", sidecar_file])
    base_cmd.append("-v")

    # Thread/Job Control
    env = os.environ.copy()
    safe_jobs = 1
    if options:
        safe_jobs = max(1, int(options.get("max_cpu_threads", 2)))
    
    env["OMP_THREAD_LIMIT"] = "1"
    base_cmd.extend(["--jobs", str(safe_jobs)])

    # GPU Setup
    tess_cfg_path = None
    use_gpu = options.get("use_gpu") if options else False
    
    # Function to execute command
    def execute_attempt(is_gpu_attempt):
        nonlocal tess_cfg_path
        cmd = list(base_cmd)
        
        if is_gpu_attempt:
            try:
                temp_dir = os.path.dirname(output_path) if os.path.dirname(output_path) else tempfile.gettempdir()
                tess_cfg_path = os.path.join(temp_dir, "tess_gpu_config.cfg")
                with open(tess_cfg_path, "w") as f:
                    f.write("tessedit_enable_opencl 1\n")
                cmd.extend(["--tesseract-config", tess_cfg_path])
            except: 
                pass # Fail silently, proceed with cmd
        
        cmd.extend([input_path, output_path])

        startupinfo = None
        if os.name == 'nt': 
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        global ACTIVE_PROCESS
        
        if os.name == 'posix':
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, start_new_session=True, bufsize=1, universal_newlines=True)
        else:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP, startupinfo=startupinfo, bufsize=1, universal_newlines=True)

        ACTIVE_PROCESS = proc

        stderr_output = []
        while True:
            line = proc.stderr.readline()
            if not line and proc.poll() is not None: break
            if line:
                stderr_output.append(line)
                match = re.search(r'(?:INFO\s+-\s+|Page\s+|Scanning page\s+)(\d+)', line, re.IGNORECASE)
                if match and progress_callback:
                    try: progress_callback(int(match.group(1)))
                    except: pass
        
        rc = proc.poll()
        out = proc.stdout.read()
        err = "".join(stderr_output)
        ACTIVE_PROCESS = None
        
        if tess_cfg_path and os.path.exists(tess_cfg_path):
            try: os.remove(tess_cfg_path)
            except: pass

        if rc != 0:
            raise subprocess.CalledProcessError(rc, cmd, output=out, stderr=err)

    # Retry Logic
    try:
        execute_attempt(use_gpu)
    except subprocess.CalledProcessError as e:
        if use_gpu:
            print("GPU failed. Retrying with CPU...")
            try:
                execute_attempt(False) # Retry without GPU
            except subprocess.CalledProcessError as e2:
                raise e2 # Fail for real
        else:
            raise e # Fail if CPU mode failed

    return sidecar_file
