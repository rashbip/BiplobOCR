import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import shutil
import time
import pikepdf
import os
import subprocess
import threading
import sv_ttk
import fitz  # PyMuPDF
from PIL import Image, ImageTk

# Local imports
from ..core.constants import APP_NAME, TEMP_DIR
from ..core.ocr_engine import detect_pdf_type, run_ocr, run_tesseract_export

class PDFViewer(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.doc = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom = 1.0
        self.image_ref = None

        self.canvas = tk.Canvas(self, bg="#2b2b2b", highlightthickness=0)
        self.canvas.pack(side="top", fill="both", expand=True)

        self.controls = ttk.Frame(self)
        self.controls.pack(side="bottom", fill="x", pady=5)
        
        self.btn_prev = ttk.Button(self.controls, text="< Prev", command=self.prev_page, state="disabled")
        self.btn_prev.pack(side="left", padx=10)
        
        self.lbl_page = ttk.Label(self.controls, text="No PDF Loaded")
        self.lbl_page.pack(side="left", expand=True)
        
        self.btn_next = ttk.Button(self.controls, text="Next >", command=self.next_page, state="disabled")
        self.btn_next.pack(side="right", padx=10)

    def load_pdf(self, path, password=None):
        try:
            self.doc = fitz.open(path)
            if self.doc.needs_pass:
                if password:
                    self.doc.authenticate(password)
                else:
                    messagebox.showerror("Error", "Password needed for preview.")
                    return
            
            self.total_pages = len(self.doc)
            self.current_page = 0
            self.show_page()
            self.lbl_page.config(text=f"Page 1 / {self.total_pages}")
            self.btn_prev.config(state="normal")
            self.btn_next.config(state="normal")
        except Exception as e:
            messagebox.showerror("Preview Error", str(e))

    def show_page(self):
        if not self.doc:
            return
            
        page = self.doc.load_page(self.current_page)
        pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom, self.zoom))
        img_data = pix.tobytes("ppm")
        
        # Resize if larger than canvas
        # For simplicity, we just display as is or basic fitting could be done, 
        # but let's stick to simple render for now.
        
        self.image_ref = ImageTk.PhotoImage(data=img_data)
        
        # Center image
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 10: cw = 600
        if ch < 10: ch = 800
        
        self.canvas.delete("all")
        self.canvas.create_image(cw//2, ch//2, image=self.image_ref, anchor="center")
        self.lbl_page.config(text=f"Page {self.current_page + 1} / {self.total_pages}")

    def next_page(self):
        if self.doc and self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.show_page()

    def prev_page(self):
        if self.doc and self.current_page > 0:
            self.current_page -= 1
            self.show_page()


class BiplobOCR(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1000x700")
        self.iconbitmap() # Set icon if available
        
        # Apply "Insane" Design
        try:
            sv_ttk.set_theme("dark")
        except:
            pass # Fallback if not installed handled safely
        
        self.current_pdf_path = None
        self.current_pdf_password = None
        
        self.build_ui()

    def build_ui(self):
        # Main Layout: Sidebar (Left) + Content (Right)
        main_paned = ttk.PanedWindow(self, orient="horizontal")
        main_paned.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Sidebar ---
        self.sidebar = ttk.Frame(main_paned, width=250, padding=10)
        main_paned.add(self.sidebar, weight=0)

        # Title
        ttk.Label(self.sidebar, text="Biplob OCR", font=("Segoe UI Variable Display", 24, "bold")).pack(pady=(0, 20), anchor="w")
        
        # Action Buttons
        ttk.Button(self.sidebar, text="📂 Open PDF", command=self.open_pdf, style="Accent.TButton").pack(fill="x", pady=5)
        
        # Options Group
        opt_frame = ttk.LabelFrame(self.sidebar, text="OCR Options", padding=10)
        opt_frame.pack(fill="x", pady=20)
        
        self.var_deskew = tk.BooleanVar(value=True)
        self.var_clean = tk.BooleanVar(value=False)
        self.var_rotate = tk.BooleanVar(value=True)
        self.var_force = tk.BooleanVar(value=False)
        self.var_optimize = tk.StringVar(value="1")
        
        ttk.Checkbutton(opt_frame, text="Deskew (Straighten)", variable=self.var_deskew).pack(anchor="w", pady=2)
        ttk.Checkbutton(opt_frame, text="Clean Background", variable=self.var_clean).pack(anchor="w", pady=2)
        ttk.Checkbutton(opt_frame, text="Auto Rotate", variable=self.var_rotate).pack(anchor="w", pady=2)
        ttk.Checkbutton(opt_frame, text="Force OCR (Ignore Text)", variable=self.var_force).pack(anchor="w", pady=2)
        
        ttk.Label(opt_frame, text="Optimization Level:").pack(anchor="w", pady=(10, 2))
        ttk.Combobox(opt_frame, textvariable=self.var_optimize, values=["0 (None)", "1 (Fast)", "2 (Good)", "3 (Best)"], state="readonly").pack(fill="x")

        # Process Button
        self.btn_process = ttk.Button(self.sidebar, text="⚡ Start Processing", command=self.start_processing_thread, state="disabled", style="Accent.TButton")
        self.btn_process.pack(fill="x", pady=20)
        
        # Status / Progress
        ttk.Label(self.sidebar, text="Status:").pack(anchor="w", pady=(20, 5))
        self.lbl_status = ttk.Label(self.sidebar, text="Idle", foreground="#aaaaaa", wraplength=200)
        self.lbl_status.pack(anchor="w")
        
        self.progress = ttk.Progressbar(self.sidebar, mode="indeterminate")
        self.progress.pack(fill="x", pady=10)

        # --- Content Area ---
        content_frame = ttk.Frame(main_paned)
        main_paned.add(content_frame, weight=1)
        
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # Tab 1: Viewer
        self.viewer = PDFViewer(self.notebook)
        self.notebook.add(self.viewer, text="  PDF Preview  ")
        
        # Tab 2: Logs (Console)
        self.log_text = tk.Text(self.notebook, state="disabled", wrap="word", font=("Consolas", 10))
        self.notebook.add(self.log_text, text="  Process Logs  ")

    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def open_pdf(self):
        pdf = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not pdf: return
        
        self.current_pdf_path = pdf
        self.log(f"Loaded: {pdf}")
        
        # Check password
        self.current_pdf_password = None
        try:
            with pikepdf.open(pdf): pass
        except pikepdf.PasswordError:
            self.current_pdf_password = simpledialog.askstring("Password", "Enter PDF Password:", show="*")
            if not self.current_pdf_password:
                return

        # Load into Viewer
        self.viewer.load_pdf(pdf, self.current_pdf_password)
        self.lbl_status.config(text="Ready to OCR")
        self.btn_process.config(state="normal")
        
        # Auto-detect type
        ptype = detect_pdf_type(pdf)
        self.log(f"Detected Type: {ptype.upper()}")
        if ptype == "text":
            self.lbl_status.config(text="Warning: Text-PDF detected. Select 'Force OCR' if you want to re-do it.")
        elif ptype == "ocr":
             self.lbl_status.config(text="Warning: Existing OCR detected.")

    def start_processing_thread(self):
        # Disable UI
        self.btn_process.config(state="disabled")
        self.progress.start(10)
        self.lbl_status.config(text="Processing... Please Wait")
        
        thread = threading.Thread(target=self.run_process_logic)
        thread.daemon = True
        thread.start()

    def run_process_logic(self):
        try:
            # Gather Options
            opts = {
                "deskew": self.var_deskew.get(),
                "clean": self.var_clean.get(),
                "rotate": self.var_rotate.get(),
                "optimize": self.var_optimize.get()[0], # Get the number 0/1/2/3
            }
            force = self.var_force.get()
            
            # Temporary output filename because we ask save location LATER
            # We will use a temp file in the temp dir, then move it.
            temp_out = os.path.join(TEMP_DIR, "processed_output.pdf")
            
            self.log("Starting OCR engine...")
            
            sidecar = run_ocr(
                self.current_pdf_path, 
                temp_out, 
                self.current_pdf_password, 
                force,
                options=opts
            )
            
            self.log("OCR Completed Successfully.")
            
            # Use `after` to interact with GUI from thread
            self.after(0, lambda: self.on_process_success(temp_out, sidecar))
            
        except subprocess.CalledProcessError as e:
            err_text = e.stderr.lower() if e.stderr else ""
            if "priorocrfounderror" in err_text or "page already has text" in err_text:
                self.after(0, lambda: self.ask_force_continuation(err_text))
            else:
                 self.after(0, lambda: self.on_process_fail(str(e.stderr)))
        except Exception as e:
             self.after(0, lambda: self.on_process_fail(str(e)))

    def ask_force_continuation(self, err_text):
        self.progress.stop()
        proceed = messagebox.askyesno(
            "Text Found", 
            "The PDF already has text. Do you want to FORCE OCR?\n(This will restart the process)"
        )
        if proceed:
            self.var_force.set(True)
            self.start_processing_thread()
        else:
            self.on_process_fail("Aborted by user (Text found).")

    def on_process_fail(self, error_msg):
        self.progress.stop()
        self.btn_process.config(state="normal")
        self.lbl_status.config(text="Failed.")
        self.log(f"ERROR: {error_msg}")
        messagebox.showerror("Error", "Processing Failed. See logs for details.")

    def on_process_success(self, temp_out_path, sidecar):
        self.progress.stop()
        self.btn_process.config(state="normal")
        self.lbl_status.config(text="Done! Saving...")
        
        # Now ask where to save
        final_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save Processed PDF"
        )
        
        if final_path:
            shutil.copy(temp_out_path, final_path)
            self.log(f"Saved PDF to: {final_path}")
            messagebox.showinfo("Success", f"PDF Saved Successfully!\n{final_path}")
            
            # Ask for sidecar export
            self.ask_export_formats(sidecar)
        else:
            self.log("Save cancelled. Temp file remains.")

    def ask_export_formats(self, sidecar):
        win = tk.Toplevel(self)
        win.title("Export Text/Data")
        win.geometry("300x200")
        
        ttk.Label(win, text="Processing Complete!").pack(pady=10)
        ttk.Label(win, text="Do you want to export text data?", foreground="gray").pack(pady=5)
        
        def save_txt():
            f = filedialog.asksaveasfilename(defaultextension=".txt", title="Save Plain Text")
            if f:
                shutil.copy(sidecar, f)
                messagebox.showinfo("Saved", "Text saved.")
        
        def save_hocr():
            f = filedialog.asksaveasfilename(defaultextension=".hocr", title="Save hOCR")
            if f:
                # We need to run tesseract export on the NEW pdf
                # But for now, let's keep it simple: we just exported PDF. 
                # Re-running tesseract on the output PDF is easiest way to get hOCR if we didn't keep it.
                # Actually, OCRmyPDF creates a sidecar (which is text).
                # To get hOCR properly, we might need to use tesseract on the output.
                # Re-using the logic from before:
                try:
                    out_base = f.replace(".hocr", "")
                    run_tesseract_export(self.current_pdf_path, out_base, "hocr") # Not ideal, but functional
                    messagebox.showinfo("Saved", "hOCR export starting (check background)")
                except:
                    pass
        
        ttk.Button(win, text="Save as .TXT", command=save_txt).pack(fill="x", padx=20, pady=5)
#        ttk.Button(win, text="Export hOCR", command=save_hocr).pack(fill="x", padx=20, pady=5) # Disabled for simplicity of this turn
        ttk.Button(win, text="Done / Close", command=win.destroy).pack(fill="x", padx=20, pady=20)
