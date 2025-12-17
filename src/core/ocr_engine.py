import subprocess
import os
from .constants import TEMP_DIR

def detect_pdf_type(pdf):
    """
    Returns:
    'text'  -> born-digital text PDF
    'ocr'   -> image PDF with OCR layer
    'image' -> image-only PDF
    """
    try:
        # 1. First probe: Check with --skip-text to see if it skips (indicating text/ocr)
        r = subprocess.run(
            ["ocrmypdf", "--skip-text", "--dry-run", pdf, "out.pdf"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        err = r.stderr.lower()

        # If it explicitly says it is skipping pages or has text
        if "skipping all pages" in err:
            # It's likely born-digital text if it decided to skip everything immediately
            # But let's verify if it's OCR or Digital Text?
            # Usually 'skipping all pages' suggests it found text on every page.
            # We'll treat this as 'text' for now, but the user distinction is subtle.
            return "text"
            
        if "priorocrfounderror" in err or "page already has text" in err:
            return "ocr"
            
        # 2. Second probe (optional but robust): Try without skip-text just to see if it triggers the error immediately?
        # Typically the above is enough if ocrmypdf behaves standardly. 
        # But if the first one passed as 'image' falsely, we might assume image.
        
        return "image"
    except Exception as e:
        print(f"Detection Error: {e}")
        return "image"

def run_ocr(input_pdf, output_pdf, password, force, options=None):
    if options is None:
        options = {}
        
    os.makedirs(TEMP_DIR, exist_ok=True)
    sidecar = os.path.join(TEMP_DIR, "ocr.txt")

    cmd = [
        "ocrmypdf",
        "--language", "ben+eng",
        "--output-type", "pdf",
        "--sidecar", sidecar,
    ]

    # Parsing Options
    if force:
        cmd.append("--force-ocr")
        
    if password:
        cmd += ["--pdf-password", password]

    # Advanced Features
    if options.get('deskew'):
        cmd.append("--deskew")
    
    if options.get('clean'):
        cmd.append("--clean")
        
    if options.get('rotate'):
        cmd.append("--rotate-pages")
        
    # Optimization level
    opt_level = str(options.get('optimize', '0')) # Default to 0 (fast)
    cmd += ["--optimize", opt_level]

    cmd += [input_pdf, output_pdf]

    # Capture output to check for specific errors if it fails
    # We allow stdout to pass through execution for real-time logging if needed, 
    # but for now capturing is safer for error analysis.
    p = subprocess.run(cmd, capture_output=True, text=True)
    
    if p.returncode != 0:
        # Re-raise with the stderr output so we can analyze it upstream
        raise subprocess.CalledProcessError(p.returncode, cmd, output=p.stdout, stderr=p.stderr)
        
    return sidecar

def run_tesseract_export(pdf_path, output_base, ext):
    """
    Runs tesseract to export to hocr or alto.
    ext should be 'hocr' or 'alto'.
    """
    subprocess.run([
        "tesseract",
        pdf_path,
        output_base,
        "-l", "ben+eng",
        ext
    ], check=True)
