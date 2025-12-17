import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import shutil
import time
import pikepdf
import os
import subprocess
import threading
import fitz  # PyMuPDF
from PIL import Image, ImageTk

# Local imports
from ..core.constants import APP_NAME, TEMP_DIR
from ..core.ocr_engine import detect_pdf_type, run_ocr, run_tesseract_export
from ..core.config_manager import state as app_state
from .pdf_viewer import PDFViewer
from .settings_dialog import SettingsDialog

# Import sv_ttk conditionally or manage theme manually
try:
    import sv_ttk
except ImportError:
    sv_ttk = None

class BiplobOCR(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw() # Hide until setup done
        self.load_settings()
        
        self.title(app_state.t("app_title"))
        self.geometry("1100x750")
        
        self.build_ui()
        self.deiconify()

    def load_settings(self):
        # Apply theme
        theme = app_state.get("theme")
        if sv_ttk:
            if theme == "dark":
                sv_ttk.set_theme("dark")
            elif theme == "light":
                sv_ttk.set_theme("light")
            else:
                try:
                    import darkdetect
                    is_dark = darkdetect.isDark()
                    sv_ttk.set_theme("dark" if is_dark else "light")
                except:
                    sv_ttk.set_theme("light") 

    def open_settings(self):
        SettingsDialog(self)

    def build_ui(self):
        # Top Menubar (for Settings)
        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)
        
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open...", command=self.open_pdf)
        file_menu.add_command(label="Exit", command=self.quit)
        
        self.menubar.add_command(label="⚙️ " + app_state.t("settings_title"), command=self.open_settings)
        
        # Main Layout
        self.paned = ttk.PanedWindow(self, orient="horizontal")
        self.paned.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Sidebar ---
        self.sidebar = ttk.Frame(self.paned, width=280, padding=15)
        self.paned.add(self.sidebar, weight=0)

        # Title
        ttk.Label(self.sidebar, text=app_state.t("app_title"), font=("Segoe UI Variable Display", 22, "bold")).pack(pady=(0, 20), anchor="w")
        
        # Open Button
        ttk.Button(self.sidebar, text=app_state.t("btn_open"), command=self.open_pdf, style="Accent.TButton").pack(fill="x", pady=5)
        
        # Options Group
        opt_frame = ttk.LabelFrame(self.sidebar, text=app_state.t("grp_options"), padding=10)
        opt_frame.pack(fill="x", pady=20)
        
        # Load Defaults from persistent state (defaulting to False as requested)
        self.var_deskew = tk.BooleanVar(value=app_state.get_option("deskew"))
        self.var_clean = tk.BooleanVar(value=app_state.get_option("clean"))
        self.var_rotate = tk.BooleanVar(value=app_state.get_option("rotate"))
        self.var_force = tk.BooleanVar(value=app_state.get_option("force"))
        self.var_optimize = tk.StringVar(value=app_state.get_option("optimize"))
        
        ttk.Checkbutton(opt_frame, text=app_state.t("opt_deskew"), variable=self.var_deskew).pack(anchor="w", pady=2)
        ttk.Checkbutton(opt_frame, text=app_state.t("opt_clean"), variable=self.var_clean).pack(anchor="w", pady=2)
        ttk.Checkbutton(opt_frame, text=app_state.t("opt_rotate"), variable=self.var_rotate).pack(anchor="w", pady=2)
        ttk.Checkbutton(opt_frame, text=app_state.t("opt_force"), variable=self.var_force).pack(anchor="w", pady=2)
        
        ttk.Label(opt_frame, text=app_state.t("lbl_optimize")).pack(anchor="w", pady=(10, 2))
        ttk.Combobox(opt_frame, textvariable=self.var_optimize, values=["0", "1", "2", "3"], state="readonly").pack(fill="x")

        # Process Button
        self.btn_process = ttk.Button(self.sidebar, text=app_state.t("btn_process"), command=self.start_processing_thread, state="disabled", style="Accent.TButton")
        self.btn_process.pack(fill="x", pady=20)
        
        # Status
        self.lbl_status = ttk.Label(self.sidebar, text=app_state.t("lbl_status_idle"), foreground="gray", wraplength=250)
        self.lbl_status.pack(anchor="w", pady=5)
        
        self.progress = ttk.Progressbar(self.sidebar, mode="indeterminate")
        self.progress.pack(fill="x", pady=5)

        # --- Content Area ---
        self.content_frame = ttk.Frame(self.paned)
        self.paned.add(self.content_frame, weight=1)
        
        # We use a container to swap between "Viewer" and "Success View"
        self.view_container = ttk.Frame(self.content_frame)
        self.view_container.pack(fill="both", expand=True)
        
        self.viewer = PDFViewer(self.view_container)
        self.viewer.pack(fill="both", expand=True)

        # Success View (Created but hidden)
        self.success_frame = ttk.Frame(self.content_frame)
        # We will pack this when needed by hiding view_container

    # --- Actions ---
    
    def reload_ui(self):
        # Restart is safer for Tkinter translation updates.
        messagebox.showinfo("Restart Required", "Please restart the application to apply changes fully.")
        self.destroy()

    def open_pdf(self):
        pdf = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not pdf: return
        self.current_pdf_path = pdf
        
        # Determine password
        password = None
        try:
            with pikepdf.open(pdf): pass
        except pikepdf.PasswordError:
            password = simpledialog.askstring("Password", "Enter PDF Password:", show="*")
            if not password: return
        
        self.current_pdf_password = password
        self.viewer.load_pdf(pdf, password)
        self.btn_process.config(state="normal")
        
        # Show viewer, hide success if open
        self.success_frame.pack_forget()
        self.view_container.pack(fill="both", expand=True)
        self.lbl_status.config(text=f"Loaded: {os.path.basename(pdf)}")

    def start_processing_thread(self):
        # Save current options to state
        app_state.set_option("deskew", self.var_deskew.get())
        app_state.set_option("clean", self.var_clean.get())
        app_state.set_option("rotate", self.var_rotate.get())
        app_state.set_option("force", self.var_force.get())
        app_state.set_option("optimize", self.var_optimize.get())
        app_state.save_config({}) # Persist to disk

        self.btn_process.config(state="disabled")
        self.progress.start(10)
        self.lbl_status.config(text=app_state.t("lbl_status_processing"))
        
        thread = threading.Thread(target=self.run_process_logic)
        thread.daemon = True
        thread.start()

    def run_process_logic(self):
        try:
            opts = {
                "deskew": self.var_deskew.get(),
                "clean": self.var_clean.get(),
                "rotate": self.var_rotate.get(),
                "optimize": self.var_optimize.get(),
            }
            temp_out = os.path.join(TEMP_DIR, "processed_output.pdf")
            
            sidecar = run_ocr(
                self.current_pdf_path, 
                temp_out, 
                self.current_pdf_password, 
                self.var_force.get(),
                options=opts
            )
            self.after(0, lambda: self.on_process_success(temp_out, sidecar))
            
        except subprocess.CalledProcessError as e:
            err_text = str(e.stderr).lower() if e.stderr else ""
            if "priorocrfounderror" in err_text or "page already has text" in err_text:
                self.after(0, lambda: self.ask_force_continuation())
            else:
                self.after(0, lambda: self.on_process_fail(str(e.stderr)))
        except Exception as e:
            self.after(0, lambda: self.on_process_fail(str(e)))

    def on_process_fail(self, msg):
        self.progress.stop()
        self.btn_process.config(state="normal")
        self.lbl_status.config(text="Failed: " + msg[:30])
        messagebox.showerror("Error", msg)

    def ask_force_continuation(self):
        self.progress.stop()
        proceed = messagebox.askyesno("Text Detected", "Files already has text. Force OCR?")
        if proceed:
            self.var_force.set(True)
            self.start_processing_thread()
        else:
            self.on_process_fail("Aborted.")

    def on_process_success(self, temp_out, sidecar):
        self.progress.stop()
        self.btn_process.config(state="normal")
        self.lbl_status.config(text=app_state.t("lbl_status_done"))
        
        # Show Success UI in Center
        self.view_container.pack_forget()
        self.show_success_ui(temp_out, sidecar)

    def show_success_ui(self, temp_out, sidecar):
        # Clear previous
        for widget in self.success_frame.winfo_children():
            widget.destroy()
        
        self.success_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Center Content
        center = ttk.Frame(self.success_frame)
        center.place(relx=0.5, rely=0.5, anchor="center")
        
        ttk.Label(center, text="✅ " + app_state.t("msg_success"), font=("Segoe UI", 25)).pack(pady=20)
        ttk.Label(center, text=app_state.t("lbl_export_prompt"), font=("Segoe UI", 12)).pack(pady=10)
        
        btn_frame = ttk.Frame(center)
        btn_frame.pack(pady=20)
        
        # 1. Save PDF
        def save_pdf():
            f = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
            if f:
                shutil.copy(temp_out, f)
                messagebox.showinfo("Saved", f"PDF Saved to {f}")

        # 2. Save Text
        def save_txt():
            f = filedialog.asksaveasfilename(defaultextension=".txt")
            if f:
                shutil.copy(sidecar, f)
                messagebox.showinfo("Saved", "Text Saved.")

        # 3. Save hOCR
        def save_hocr():
            f = filedialog.asksaveasfilename(defaultextension=".hocr")
            if f:
                # Mock call or real call
                try:
                    run_tesseract_export(self.current_pdf_path, f.replace(".hocr", ""), "hocr")
                    messagebox.showinfo("Saved", "hOCR Saved.")
                except:
                    messagebox.showerror("Error", "Export failed.")

        ttk.Button(btn_frame, text="💾 Save Final PDF", command=save_pdf, style="Accent.TButton", width=25).pack(pady=5)
        ttk.Button(btn_frame, text="📄 " + app_state.t("btn_save_txt"), command=save_txt, width=25).pack(pady=5)
        ttk.Button(btn_frame, text="📑 " + app_state.t("btn_save_hocr"), command=save_hocr, width=25).pack(pady=5)
        
        ttk.Button(center, text=app_state.t("btn_close_export"), command=self.close_success_ui).pack(pady=20)

    def close_success_ui(self):
        self.success_frame.pack_forget()
        self.view_container.pack(fill="both", expand=True)
