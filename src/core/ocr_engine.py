
import subprocess
import os
import signal
import re
import shutil
import tempfile
import sys
import math
import logging
from .constants import APP_NAME, TEMP_DIR
from . import platform_utils

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Try importing dependencies safely to avoid immediate crashes
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None
    logging.warning("PyMuPDF (fitz) not found. PDF detection may be limited.")

try:
    import pikepdf
except ImportError:
    pikepdf = None
    logging.warning("pikepdf not found. PDF operations will be restricted.")

# Store active process for cancellation
ACTIVE_PROCESS = None
CANCEL_FLAG = False

class OCRError(Exception):
    """Custom Exception for OCR errors to provide better user feedback."""
    pass

# Initialize environment immediately
platform_utils.setup_tesseract_environment()

def get_tessdata_dir():
    return platform_utils.get_tessdata_dir()

def get_available_languages():
    d = get_tessdata_dir()
    if not os.path.exists(d): return ["eng"]
    langs = []
    for f in os.listdir(d):
        if f.endswith(".traineddata") and f != "osd.traineddata":
            langs.append(f.replace(".traineddata", ""))
    return sorted(langs) if langs else ["eng"]

def detect_pdf_type(file_path, password=None):
    """
    Check if PDF is text-based (Digital), scanned images, or encrypted.
    Returns: 'text', 'image', 'mixed', 'encrypted', or 'unknown'
    """
    if not fitz:
        return 'unknown'

    try:
        doc = fitz.open(file_path)
        
        if doc.is_encrypted:
            if password:
                try:
                    doc.authenticate(password)
                except:
                    return 'encrypted' # Auth failed
            else:
                return 'encrypted'

        has_text = False
        has_images = False
        
        # Check first 10 pages to save time on huge docs, or all if small
        check_pages = min(len(doc), 15)
        
        for i in range(check_pages):
            page = doc[i]
            if page.get_text().strip():
                has_text = True
            if page.get_images():
                has_images = True
                
        doc.close()
        
        if has_text and not has_images: return 'text'
        if has_images and not has_text: return 'image'
        if has_text and has_images: return 'mixed'
        return 'image' # Default to image if empty?
        
    except Exception as e:
        logging.error(f"Error detecting PDF type: {e}")
        return 'unknown'

def cancel_ocr():
    """
    Terminates the currently running OCR process and its children.
    """
    global ACTIVE_PROCESS, CANCEL_FLAG
    CANCEL_FLAG = True
    
    if ACTIVE_PROCESS:
        try:
            platform_utils.kill_process_tree(ACTIVE_PROCESS.pid)
            ACTIVE_PROCESS = None
        except Exception as e:
            logging.error(f"Error killing process: {e}")

def _decrypt_pdf(input_path, password):
    """
    Decrypts a PDF using pikepdf and saves it to a temporary file.
    Returns the path to the temporary decrypted file.
    """
    if not pikepdf:
        raise OCRError("pikepdf module missing. Cannot handle password protected files.")
        
    try:
        temp_decrypted = os.path.join(TEMP_DIR, f"decrypted_{os.path.basename(input_path)}")
        os.makedirs(TEMP_DIR, exist_ok=True)
        
        with pikepdf.open(input_path, password=password) as pdf:
            pdf.save(temp_decrypted)
        return temp_decrypted
    except pikepdf.PasswordError:
        raise OCRError("Invalid password provided for encrypted PDF.")
    except Exception as e:
        raise OCRError(f"Failed to decrypt PDF: {str(e)}")

def _merge_pdfs(pdf_list, output_path):
    """
    Merges a list of PDFs into one output file using pikepdf.
    """
    if not pikepdf:
        raise OCRError("pikepdf module missing. Cannot merge PDF chunks.")
        
    merger = pikepdf.Pdf.new()
    for pdf_file in pdf_list:
        try:
            with pikepdf.open(pdf_file) as src:
                merger.pages.extend(src.pages)
        except Exception as e:
            logging.error(f"Error merging chunk {pdf_file}: {e}")
            raise OCRError(f"Failed to merge chunk {os.path.basename(pdf_file)}")
    
    merger.save(output_path)
    merger.close()



def run_ocr(input_path, output_path, password=None, force=False, options=None, progress_callback=None, log_callback=None):
    """
    Executes OCRmyPDF on the input file.
    
    Features:
     - Handles Password Protection (auto-decrypt)
     - Handles Large Files (Chunking > 50 pages)
     - Error Management (Retry on CPU if GPU fails)
     - Resource Cleanup
    
    Args:
        input_path (str): Path to source PDF.
        output_path (str): Path to save result.
        password (str): PDF password (optional).
        force (bool): Force OCR even if text exists.
        options (dict): Options like language, deskew, clean, etc.
        progress_callback (func): Function(page_num) for updates.
        
    Returns:
        str: Path to the sidecar text file generated.
    """
    global CANCEL_FLAG
    CANCEL_FLAG = False
    
    # 1. Setup & Decryption
    working_input = input_path
    decrypted_temp = None
    
    try:
        # Detect if we need decryption
        ftype = detect_pdf_type(input_path, password)
        if password or ftype == 'encrypted':
            logging.info(f"Decrypting PDF: {input_path}")
            decrypted_temp = _decrypt_pdf(input_path, password)
            working_input = decrypted_temp

        # 2. Check File Size / Page Count for Chunking
        # Strategy: Limit chunking to ensure stability on low-mem systems
        CHUNK_THRESHOLD = 50
        CHUNK_SIZE = 20
        
        total_pages = 0
        try:
            if fitz:
                with fitz.open(working_input) as doc:
                    total_pages = len(doc)
            elif pikepdf:
                with pikepdf.open(working_input) as doc:
                    total_pages = len(doc.pages)
        except Exception: 
            total_pages = 0 # Proceed without chunking if detection fails
            
        # --- CHUNKING STRATEGY ---
        if total_pages > CHUNK_THRESHOLD and pikepdf:
            logging.info(f"Large PDF detected ({total_pages} pages). Engaging chunking mode...")
            return _run_ocr_chunked(
                working_input, output_path, total_pages, CHUNK_SIZE, 
                force, options, progress_callback, log_callback
            )
        else:
            # --- STANDARD SINGLE FILE PROCESS ---
            return _run_ocr_single(working_input, output_path, force, options, progress_callback, log_callback)
            
    except OCRError as e:
        raise e
    except Exception as e:
        raise OCRError(f"OCR Execution Failed: {str(e)}")
    finally:
        # Cleanup decrypted temp file
        if decrypted_temp and os.path.exists(decrypted_temp):
            try: os.remove(decrypted_temp)
            except: pass

def _run_ocr_chunked(input_path, output_path, total_pages, chunk_size, force, options, progress_callback, log_callback):
    """
    Splits PDF into chunks, OCRs them individually, and merges them back.
    """
    chunks_dir = os.path.join(TEMP_DIR, f"chunks_{os.getpid()}")
    os.makedirs(chunks_dir, exist_ok=True)
    
    chunk_files = []     # (path, start_page)
    processed_chunks = []
    
    try:
        # 1. Split PDF
        with pikepdf.open(input_path) as pdf:
            num_chunks = math.ceil(total_pages / chunk_size)
            
            for i in range(num_chunks):
                start_page = i * chunk_size
                end_page = min((i + 1) * chunk_size, total_pages)
                
                # Extract chunk
                dst = pikepdf.Pdf.new()
                for p in range(start_page, end_page):
                    dst.pages.append(pdf.pages[p])
                    
                chunk_name = f"chunk_{i}.pdf"
                chunk_path = os.path.join(chunks_dir, chunk_name)
                dst.save(chunk_path)
                chunk_files.append((chunk_path, start_page)) # Stores path and page offset
        
        # 2. Process Each Chunk
        for i, (c_path, offset) in enumerate(chunk_files):
            if CANCEL_FLAG: 
                raise OCRError("Process Cancelled")

            c_out = c_path.replace(".pdf", "_ocr.pdf")
            
            # Wrapper for progress callback to map chunk page -> global page
            def chunk_progress_wrapper(p):
                if progress_callback:
                    progress_callback(offset + p)
            
            logging.info(f"Processing chunk {i+1}/{len(chunk_files)}...")
            
            # Recursive call to single runner
            _run_ocr_single(c_path, c_out, force, options, chunk_progress_wrapper, log_callback)
            processed_chunks.append(c_out)
            
        # 3. Merge Results
        logging.info("Merging processed chunks...")
        _merge_pdfs(processed_chunks, output_path)
        
        # 4. Generate Sidecar Text (merged from chunks)
        sidecar_file = output_path.replace(".pdf", ".txt")
        full_text = ""
        for p_chunk in processed_chunks:
            txt_chunk = p_chunk.replace(".pdf", ".txt")
            if os.path.exists(txt_chunk):
                with open(txt_chunk, "r", encoding="utf-8", errors="ignore") as f:
                    full_text += f.read() + "\n"
        
        with open(sidecar_file, "w", encoding="utf-8") as f:
            f.write(full_text)
            
        return sidecar_file
        
    except Exception as e:
        raise OCRError(f"Chunking processing failed: {e}")
    finally:
        # Cleanup chunks directory
        try: shutil.rmtree(chunks_dir)
        except: pass

def _run_cmd(cmd, env, progress_callback=None, log_callback=None):
    """
    Executes a subprocess command and handles output/progress parsing.
    Captures stderr for progress updates from OCRmyPDF/Tesseract.
    """
    global ACTIVE_PROCESS
    
    startupinfo = platform_utils.get_subprocess_startup_info()
    
    # Process creation: Use new session/process group to allow cleanup
    # On POSIX, start_new_session=True is the way to go (setsid)
    # On Windows, CREATE_NEW_PROCESS_GROUP
    
    kwargs = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "encoding": "utf-8",
        "env": env,
        "bufsize": 1,
        "universal_newlines": True
    }
    
    if os.name == 'posix':
        kwargs["start_new_session"] = True
    else:
        kwargs["creationflags"] = platform_utils.get_subprocess_creation_flags()
        kwargs["startupinfo"] = startupinfo
        
    proc = subprocess.Popen(cmd, **kwargs)

    ACTIVE_PROCESS = proc

    stderr_output = []
    
    # Read stderr line by line for progress
    while True:
        line = proc.stderr.readline()
        if not line and proc.poll() is not None: break
        if line:
            stderr_output.append(line)
            # Send to log callback
            if log_callback:
                try: log_callback(line.rstrip())
                except: pass
                
            # OCRmyPDF/Tesseract progress pattern
            match = re.search(r'(?:INFO\s+-\s+|Page\s+|Scanning page\s+)(\d+)', line, re.IGNORECASE)
            if match and progress_callback:
                try: 
                    progress_callback(int(match.group(1)))
                except: pass
    
    rc = proc.poll()
    out = proc.stdout.read()
    err = "".join(stderr_output)
    ACTIVE_PROCESS = None

    if rc != 0:
        if log_callback: log_callback(f"Command failed with RC {rc}")
        logging.error(f"Command failed with RC {rc}: {cmd}")
        logging.error(f"STDERR ({len(err)} chars): {err}")
        raise subprocess.CalledProcessError(rc, cmd, output=out, stderr=err)
    
    return out, err

def _run_ocr_single(input_path, output_path, force, options, progress_callback, log_callback=None):
    """
    Internal function to run OCR on a single file (not password protected).
    """
    # ... (Command builder omitted for brevity, logic remains same but passes log_callback)
    # I need to verify I don't lose the cmd building logic.
    # Actually, replacing THE WHOLE function _run_ocr_single is safer or I need to update just the call site.
    # The previous prompt replaced definition only.
    # I'll paste the definition + logic.
    
    # 1. Prepare Base CMD - Use Python module execution for reliability
    # This ensures ocrmypdf works even if Scripts folder isn't in PATH
    base_cmd = [sys.executable, "-m", "ocrmypdf"]
    if force: base_cmd.append("--force-ocr")
    else: base_cmd.append("--skip-text")

    # Important: Optimize for size and compatibility
    base_cmd.extend(["--output-type", "pdf"])

    if options:
        if options.get("deskew"): base_cmd.append("--deskew")
        if options.get("clean"): base_cmd.append("--clean")
        if options.get("rotate"): base_cmd.append("--rotate-pages")
        if options.get("optimize", "0") != "0": 
            base_cmd.extend(["--optimize", options.get("optimize")])
        
        lang = options.get("language", "eng")
        base_cmd.extend(["-l", lang])
            
    sidecar_file = output_path.replace(".pdf", ".txt")
    base_cmd.extend(["--sidecar", sidecar_file])
    base_cmd.append("-v") # Verbose for progress tracking

    # Thread/Job Control
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8" # Force UTF-8 for subprocess logging
    safe_jobs = 1
    if options:
        safe_jobs = max(1, int(options.get("max_cpu_threads", 2)))
    
    env["OMP_THREAD_LIMIT"] = "1"
    base_cmd.extend(["--jobs", str(safe_jobs)])

    # GPU Setup
    tess_cfg_path = None
    use_gpu = options.get("use_gpu") if options else False
    
    # Internal execution helper with retry logic
    def attempt_execution(is_gpu):
        nonlocal tess_cfg_path
        cmd = list(base_cmd)
        
        if is_gpu:
            try:
                # Create config file for Tesseract
                temp_dir = os.path.dirname(output_path) if os.path.dirname(output_path) else tempfile.gettempdir()
                tess_cfg_path = os.path.join(temp_dir, f"tess_gpu_config_{os.getpid()}.cfg")
                with open(tess_cfg_path, "w") as f:
                    # Enable OpenCL for Tesseract
                    f.write("tessedit_enable_opencl 1\n")
                cmd.extend(["--tesseract-config", tess_cfg_path])
            except: 
                pass # Proceed without config if write fails
        
        cmd.extend([input_path, output_path])
        
        try:
            _run_cmd(cmd, env, progress_callback, log_callback) # Pass log_callback here
        except subprocess.CalledProcessError as e:
            raise e
        finally:
            if tess_cfg_path and os.path.exists(tess_cfg_path):
                try: os.remove(tess_cfg_path)
                except: pass

    # Retry Logic: GPU -> CPU -> Sanitize/Flatten
    try:
        attempt_execution(use_gpu)
    except subprocess.CalledProcessError as e:
        if CANCEL_FLAG: raise OCRError("Process Cancelled")
        
        # 1. GPU Failed? -> Try CPU
        if use_gpu:
            if log_callback: log_callback("GPU failed. Retrying with CPU...")
            logging.warning("GPU OCR mode failed. Retrying with CPU fallback...")
            try:
                attempt_execution(False)
                return sidecar_file
            except subprocess.CalledProcessError as e2:
                if CANCEL_FLAG: raise OCRError("Process Cancelled")
                last_error = e2
        else:
            last_error = e
            
        # 2. CPU Failed? -> Try Sanitizing
        if log_callback: log_callback("Standard OCR failed. Attempting sanitize...")
        logging.warning("Standard OCR failed. Attempting to sanitize PDF (Rasterize & Rebuild)...")
        sanitized_path = input_path.replace(".pdf", "_clean.pdf")
        
        if _sanitize_pdf(input_path, sanitized_path):
            try:
                cmd = list(base_cmd)
                cmd.extend([sanitized_path, output_path])
                _run_cmd(cmd, env, progress_callback, log_callback)
                return sidecar_file
            except subprocess.CalledProcessError as e3:
                err_text = e3.stderr if e3.stderr else str(e3)
                raise OCRError(f"OCR Critical Fail (Sanitized): {err_text[-500:]}")
            finally:
                if os.path.exists(sanitized_path):
                    try: os.remove(sanitized_path)
                    except: pass
        else:
            err_text = last_error.stderr if last_error.stderr else str(last_error)
            raise OCRError(f"OCR Failed: {err_text[-500:]}")

    return sidecar_file
    """
    Internal function to run OCR on a single file (not password protected).
    """
    # 1. Prepare Base CMD - Use Python module execution for reliability
    base_cmd = [sys.executable, "-m", "ocrmypdf"]
    if force: base_cmd.append("--force-ocr")
    else: base_cmd.append("--skip-text")

    # Important: Optimize for size and compatibility
    base_cmd.extend(["--output-type", "pdf"])

    if options:
        if options.get("deskew"): base_cmd.append("--deskew")
        if options.get("clean"): base_cmd.append("--clean")
        if options.get("rotate"): base_cmd.append("--rotate-pages")
        if options.get("optimize", "0") != "0": 
            base_cmd.extend(["--optimize", options.get("optimize")])
        
        lang = options.get("language", "eng")
        base_cmd.extend(["-l", lang])
            
    sidecar_file = output_path.replace(".pdf", ".txt")
    base_cmd.extend(["--sidecar", sidecar_file])
    base_cmd.append("-v") # Verbose for progress tracking

    # Thread/Job Control
    # Respect user setting or default to 1 (safe)
    env = os.environ.copy()
    safe_jobs = 1
    if options:
        safe_jobs = max(1, int(options.get("max_cpu_threads", 2)))
    
    # OMP_THREAD_LIMIT helps Tesseract not oversubscribe
    env["OMP_THREAD_LIMIT"] = "1"
    base_cmd.extend(["--jobs", str(safe_jobs)])

    # GPU Setup
    tess_cfg_path = None
    use_gpu = options.get("use_gpu") if options else False
    
    # Internal execution helper with retry logic
    def attempt_execution(is_gpu):
        nonlocal tess_cfg_path
        cmd = list(base_cmd)
        
        if is_gpu:
            try:
                # Create config file for Tesseract
                temp_dir = os.path.dirname(output_path) if os.path.dirname(output_path) else tempfile.gettempdir()
                tess_cfg_path = os.path.join(temp_dir, f"tess_gpu_config_{os.getpid()}.cfg")
                with open(tess_cfg_path, "w") as f:
                    # Enable OpenCL for Tesseract
                    f.write("tessedit_enable_opencl 1\n")
                cmd.extend(["--tesseract-config", tess_cfg_path])
            except: 
                pass # Proceed without config if write fails
        
        cmd.extend([input_path, output_path])
        
        try:
            _run_cmd(cmd, env, progress_callback)
        except subprocess.CalledProcessError as e:
            raise e
        finally:
            # Clean up tesseract config
            if tess_cfg_path and os.path.exists(tess_cfg_path):
                try: os.remove(tess_cfg_path)
                except: pass

    # Retry Logic: GPU -> CPU -> Sanitize/Flatten
    try:
        attempt_execution(use_gpu)
    except subprocess.CalledProcessError as e:
        if CANCEL_FLAG: raise OCRError("Process Cancelled")
        
        # 1. GPU Failed? -> Try CPU
        if use_gpu:
            logging.warning("GPU OCR mode failed. Retrying with CPU fallback...")
            try:
                attempt_execution(False)
                return sidecar_file
            except subprocess.CalledProcessError as e2:
                if CANCEL_FLAG: raise OCRError("Process Cancelled")
                last_error = e2
        else:
            last_error = e
            
        # 2. CPU Failed? -> Try Sanitizing (Flattening to Image)
        # This fixes "JPEG data is corrupt" or "Invalid PDF" errors
        logging.warning("Standard OCR failed. Attempting to sanitize PDF (Rasterize & Rebuild)...")
        sanitized_path = input_path.replace(".pdf", "_clean.pdf")
        
        if _sanitize_pdf(input_path, sanitized_path):
            try:
                # We must update the cmd to use the new input
                # Note: We can't easily swap input in the closure, so we call recursively or copy logic.
                # Simplest is to copy logic for this fallback:
                
                cmd = list(base_cmd)
                cmd.extend([sanitized_path, output_path])
                
                # Run with CPU env for safety
                _run_cmd(cmd, env, progress_callback)
                
                # If success, return sidecar
                return sidecar_file
                
            except subprocess.CalledProcessError as e3:
                # If even sanitized fails, raise the original or new error
                err_text = e3.stderr if e3.stderr else str(e3)
                raise OCRError(f"OCR Critical Fail (Sanitized): {err_text[-500:]}")
            finally:
                if os.path.exists(sanitized_path):
                    try: os.remove(sanitized_path)
                    except: pass
        else:
            # Sanitization couldn't run (e.g. no fitz), raise original error
            err_text = last_error.stderr if last_error.stderr else str(last_error)
            raise OCRError(f"OCR Failed: {err_text[-500:]}")

    return sidecar_file

def _sanitize_pdf(input_path, output_path):
    """
    Rebuilds a PDF by converting pages to images and back.
    Fixes corrupt streams/JPEGs that crash OCRmyPDF.
    """
    if not fitz: return False
    try:
        doc = fitz.open(input_path)
        new_doc = fitz.open()
        
        for i, page in enumerate(doc):
            # Render page to image (300 DPI for good OCR quality)
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("jpg", jpg_quality=95)
            
            # Create new page in new doc
            new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
            new_page.insert_image(page.rect, stream=img_bytes)
            
        new_doc.save(output_path)
        new_doc.close()
        doc.close()
        return True
    except Exception as e:
        logging.error(f"PDF Sanitization failed: {e}")
        return False
