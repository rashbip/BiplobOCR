import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import shutil
import time
import pikepdf
import os
import subprocess

# Local imports
from ..core.constants import APP_NAME, TEMP_DIR
from ..core.ocr_engine import detect_pdf_type, run_ocr, run_tesseract_export

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
        except subprocess.CalledProcessError as e:
            err_text = e.stderr.lower() if e.stderr else ""
            
            # Check for the specific "already has text" error
            if "priorocrfounderror" in err_text or "page already has text" in err_text:
                proceed = messagebox.askyesno(
                    "Text Detected during OCR",
                    "OCR stopped because the PDF already contains text.\n\n"
                    "Do you want to FORCE OCR? (This will re-OCR everything)"
                )
                if proceed:
                    self.status.config(text="Forcing OCR...")
                    self.update()
                    try:
                        sidecar = run_ocr(pdf, output_pdf, password, True)
                    except subprocess.CalledProcessError as e2:
                        messagebox.showerror(
                            "OCR Failed",
                            f"Failed even with force mode.\n\nError: {e2.stderr}"
                        )
                        self.status.config(text="OCR Failed.")
                        return
                else:
                    self.status.config(text="OCR Aborted.")
                    return
            else:
                # Genuine other error
                messagebox.showerror(
                    "OCR Failed",
                    f"OCRmyPDF failed.\nThe PDF may be corrupted or unsupported.\n\nError: {str(e.stderr)[:200]}..." # truncated log
                )
                self.status.config(text="OCR Failed.")
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
        
        # Remove extension for tesseract output base
        output_base = out.replace(f".{ext}", "")
        
        try:
            run_tesseract_export(pdf, output_base, ext)
            messagebox.showinfo("Success", f"Exported to {out}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))
