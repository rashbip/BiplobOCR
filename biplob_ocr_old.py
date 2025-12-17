import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import subprocess
import os
import shutil
import time
import pikepdf

APP_NAME = "Biplob OCR"
TEMP_DIR = "_biplob_temp"

# ---------- PDF TYPE DETECTION ----------
def detect_pdf_type(pdf):
    """
    Returns:
    'text'  -> born-digital text PDF
    'ocr'   -> image PDF with OCR layer
    'image' -> image-only PDF
    """
    try:
        r = subprocess.run(
            ["ocrmypdf", "--skip-text", "--dry-run", pdf, "out.pdf"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        err = r.stderr.lower()

        if "skipping all pages" in err:
            return "text"
        if "page already has text" in err:
            return "ocr"
        return "image"
    except:
        return "image"

# ---------- OCR RUN ----------
def run_ocr(input_pdf, output_pdf, password, force):
    os.makedirs(TEMP_DIR, exist_ok=True)
    sidecar = os.path.join(TEMP_DIR, "ocr.txt")

    cmd = [
        "ocrmypdf",
        "--language", "ben+eng",
        "--output-type", "pdf",
        "--optimize", "0",
        "--sidecar", sidecar,
    ]

    if force:
        cmd.append("--force-ocr")

    if password:
        cmd += ["--pdf-password", password]

    cmd += [input_pdf, output_pdf]

    subprocess.run(cmd, check=True)
    return sidecar

# ---------- GUI ----------
class BiplobOCR(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("500x320")
        self.resizable(False, False)
        self.build_ui()

    def build_ui(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=APP_NAME, font=("Segoe UI", 20)).pack(pady=10)

        ttk.Button(
            frame,
            text="Select PDF and OCR",
            command=self.start_ocr,
            width=32
        ).pack(pady=30)

        self.status = ttk.Label(frame, text="", foreground="blue")
        self.status.pack()

    # ---------- MAIN FLOW ----------
    def start_ocr(self):
        pdf = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf")]
        )
        if not pdf:
            return

        # Password check
        password = None
        try:
            with pikepdf.open(pdf):
                pass
        except pikepdf.PasswordError:
            password = simpledialog.askstring(
                "Password Required",
                "Enter PDF password:",
                show="*"
            )
            if not password:
                return

        pdf_type = detect_pdf_type(pdf)

        # Decide force flag BEFORE OCRmyPDF
        if pdf_type == "text":
            proceed = messagebox.askyesno(
                "Text-based PDF detected",
                "This PDF already contains selectable text.\n\n"
                "OCR is NOT recommended.\n\n"
                "Do you still want to OCR it?"
            )
            if not proceed:
                return
            force = True

        elif pdf_type == "ocr":
            self.status.config(
                text="Existing OCR detected. Re-OCRing in 3 seconds..."
            )
            self.update()
            time.sleep(3)
            force = True

        else:
            # image-only
            force = False

        output_pdf = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not output_pdf:
            return

        self.status.config(text="OCR in progress...")
        self.update()

        try:
            sidecar = run_ocr(pdf, output_pdf, password, force)
        except subprocess.CalledProcessError:
            messagebox.showerror(
                "OCR Failed",
                "OCRmyPDF failed.\nThe PDF may be corrupted or unsupported."
            )
            return

        self.status.config(text="OCR completed.")
        self.after_ocr_actions(sidecar)

    # ---------- POST ACTIONS ----------
    def after_ocr_actions(self, sidecar):
        choice = messagebox.askyesnocancel(
            "Next",
            "YES = Save OCR text (.txt)\n"
            "NO = Export hOCR / ALTO\n"
            "CANCEL = Quit"
        )

        if choice is True:
            dest = filedialog.asksaveasfilename(
                defaultextension=".txt"
            )
            if dest:
                shutil.copy(sidecar, dest)

        elif choice is False:
            self.export_structured()

        shutil.rmtree(TEMP_DIR, ignore_errors=True)

    def export_structured(self):
        fmt = messagebox.askquestion(
            "Choose format",
            "YES = hOCR\nNO = ALTO"
        )

        ext = "hocr" if fmt == "yes" else "alto"

        pdf = filedialog.askopenfilename(
            title="Select the OCRed PDF",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not pdf:
            return

        out = filedialog.asksaveasfilename(
            defaultextension=f".{ext}"
        )
        if not out:
            return

        subprocess.run([
            "tesseract",
            pdf,
            out.replace(f".{ext}", ""),
            "-l", "ben+eng",
            ext
        ])

# ---------- RUN ----------
if __name__ == "__main__":
    BiplobOCR().mainloop()
