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
        self.withdraw()
        self.load_settings()
        
        self.title(app_state.t("app_title"))
        self.geometry("1200x800")
        self.minsize(900, 600)
        
        self.current_pdf_path = None
        self.current_pdf_password = None
        
        self.build_ui()
        self.deiconify()

    def load_settings(self):
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

    def build_ui(self):
        # --- Main Layout (Nav Rail + Content) ---
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill="both", expand=True)

        # 1. Navigation Rail (Left)
        self.nav_rail = ttk.Frame(self.main_container, padding=10, width=80)
        self.nav_rail.pack(side="left", fill="y")
        
        # App Icon / Title (Short)
        ttk.Label(self.nav_rail, text="B", font=("Segoe UI", 30, "bold"), foreground="#007acc").pack(pady=20)

        # Nav Buttons (Using Unicode Icons for simplicity)
        self.btn_home = ttk.Button(self.nav_rail, text="🏠\nHome", command=lambda: self.switch_tab("home"), style="Accent.TButton", width=6)
        self.btn_home.pack(pady=10)

        self.btn_scan = ttk.Button(self.nav_rail, text="⚡\nOCR", command=lambda: self.switch_tab("scan"), width=6)
        self.btn_scan.pack(pady=10)
        
        self.btn_settings = ttk.Button(self.nav_rail, text="⚙️\nSet...", command=lambda: self.switch_tab("settings"), width=6)
        self.btn_settings.pack(side="bottom", pady=20)

        # Separator
        ttk.Separator(self.main_container, orient="vertical").pack(side="left", fill="y")

        # 2. Content Stack (Right)
        self.content_area = ttk.Frame(self.main_container)
        self.content_area.pack(side="left", fill="both", expand=True)
        
        # --- VIEWS ---
        self.view_home = ttk.Frame(self.content_area, padding=40)
        self.view_scan = ttk.Frame(self.content_area) # Will hold PDF + Sidebar
        self.view_settings = ttk.SettingsView(self.content_area) if hasattr(ttk, 'SettingsView') else ttk.Frame(self.content_area, padding=40) # Custom logic below

        # Build Home
        self.build_home_view()
        
        # Build Scan
        self.build_scan_view()
        
        # Build Settings
        self.build_settings_view()

        # Init
        self.switch_tab("home")
    
    def switch_tab(self, tab):
        # Hide all
        self.view_home.pack_forget()
        self.view_scan.pack_forget()
        self.view_settings.pack_forget()
        
        # Reset styles
        self.btn_home.configure(style="TButton")
        self.btn_scan.configure(style="TButton")
        self.btn_settings.configure(style="TButton")

        if tab == "home":
            self.view_home.pack(fill="both", expand=True)
            self.btn_home.configure(style="Accent.TButton")
        elif tab == "scan":
            self.view_scan.pack(fill="both", expand=True)
            self.btn_scan.configure(style="Accent.TButton")
        elif tab == "settings":
            self.view_settings.pack(fill="both", expand=True)
            self.btn_settings.configure(style="Accent.TButton")

    def build_home_view(self):
        # Big hero section
        ttk.Label(self.view_home, text=app_state.t("app_title"), font=("Segoe UI Variable Display", 32, "bold")).pack(pady=(50, 10))
        ttk.Label(self.view_home, text="Professional PDF OCR Solution", font=("Segoe UI", 16), foreground="gray").pack(pady=(0, 40))
        
        btn_frame = ttk.Frame(self.view_home)
        btn_frame.pack()
        
        ttk.Button(btn_frame, text="📂 Open PDF", style="Accent.TButton", command=self.open_pdf_from_home, padding=10).pack(ipadx=20, ipady=5)
    
    def open_pdf_from_home(self):
        self.switch_tab("scan")
        self.open_pdf()

    def build_scan_view(self):
        # Sidebar + Viewer Layout
        self.scan_paned = ttk.PanedWindow(self.view_scan, orient="horizontal")
        self.scan_paned.pack(fill="both", expand=True)

        # Sidebar
        self.scan_sidebar = ttk.Frame(self.scan_paned, width=250, padding=10)
        self.scan_paned.add(self.scan_sidebar, weight=0)
        
        # Scan Sidebar Content (Simplified)
        ttk.Label(self.scan_sidebar, text="Tools", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=10)
        
        ttk.Button(self.scan_sidebar, text="📂 Open New", command=self.open_pdf).pack(fill="x", pady=2)
        
        opt_frame = ttk.LabelFrame(self.scan_sidebar, text=app_state.t("grp_options"), padding=10)
        opt_frame.pack(fill="x", pady=20)

        # Variables
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

        self.btn_process = ttk.Button(self.scan_sidebar, text=app_state.t("btn_process"), command=self.start_processing_thread, state="disabled", style="Accent.TButton")
        self.btn_process.pack(fill="x", pady=20)
        
        # Status
        self.lbl_status = ttk.Label(self.scan_sidebar, text=app_state.t("lbl_status_idle"), foreground="gray", wraplength=150)
        self.lbl_status.pack(anchor="w", pady=5)
        self.progress = ttk.Progressbar(self.scan_sidebar, mode="indeterminate")
        self.progress.pack(fill="x")

        # Viewer Area
        self.viewer_container = ttk.Frame(self.scan_paned)
        self.scan_paned.add(self.viewer_container, weight=1)
        
        self.viewer = PDFViewer(self.viewer_container)
        self.viewer.pack(fill="both", expand=True)
        
        # Success Overlay (Initially Hidden)
        self.success_frame = ttk.Frame(self.viewer_container, style="Card.TFrame", padding=20)

    def build_settings_view(self):
        # Use inline settings
        lbl = ttk.Label(self.view_settings, text=app_state.t("settings_title"), font=("Segoe UI", 20, "bold"))
        lbl.pack(anchor="w", pady=(0, 20))

        # General
        f = ttk.LabelFrame(self.view_settings, text="General", padding=20)
        f.pack(fill="x", pady=10)
        
        ttk.Label(f, text=app_state.t("lbl_lang")).pack(anchor="w")
        self.var_lang = tk.StringVar(value=app_state.get("language", "en"))
        cb_lang = ttk.Combobox(f, textvariable=self.var_lang, values=["en", "bn"], state="readonly")
        cb_lang.pack(fill="x", pady=(5, 10))
        cb_lang.bind("<<ComboboxSelected>>", lambda e: self.save_settings_inline())

        ttk.Label(f, text=app_state.t("lbl_theme")).pack(anchor="w")
        self.var_theme = tk.StringVar(value=app_state.get("theme", "system"))
        cb_theme = ttk.Combobox(f, textvariable=self.var_theme, values=["system", "dark", "light"], state="readonly")
        cb_theme.pack(fill="x", pady=(5, 10))
        cb_theme.bind("<<ComboboxSelected>>", lambda e: self.save_settings_inline())

        ttk.Label(self.view_settings, text="Changes require restart to fully apply UI text translations.", foreground="gray").pack(pady=20)
        
    def save_settings_inline(self):
        new_conf = {
            "language": self.var_lang.get(),
            "theme": self.var_theme.get()
        }
        app_state.save_config(new_conf)
        # Apply theme immediately if possible
        if self.var_theme.get() != "system":
            if sv_ttk: sv_ttk.set_theme(self.var_theme.get())

    # --- Actions ---
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
        
        # Hide success if showing
        self.success_frame.place_forget()
        self.lbl_status.config(text=f"Loaded: {os.path.basename(pdf)}")

    def start_processing_thread(self):
        app_state.set_option("deskew", self.var_deskew.get())
        app_state.set_option("clean", self.var_clean.get())
        app_state.set_option("rotate", self.var_rotate.get())
        app_state.set_option("force", self.var_force.get())
        app_state.set_option("optimize", self.var_optimize.get())
        app_state.save_config({})

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
        self.lbl_status.config(text="Failed.")
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
        
        self.show_success_ui(temp_out, sidecar)

    def show_success_ui(self, temp_out, sidecar):
        self.success_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        # Clear childs
        for c in self.success_frame.winfo_children(): c.destroy()
        
        # Center
        c = ttk.Frame(self.success_frame)
        c.place(relx=0.5, rely=0.5, anchor="center")
        
        ttk.Label(c, text="✅ " + app_state.t("msg_success"), font=("Segoe UI", 24)).pack(pady=10)
        
        def save_pdf():
            f = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
            if f:
                shutil.copy(temp_out, f)
                messagebox.showinfo("Saved", "PDF Saved!")

        def save_txt():
            f = filedialog.asksaveasfilename(defaultextension=".txt")
            if f:
                shutil.copy(sidecar, f)
                messagebox.showinfo("Saved", "Text Saved!")
        
        def close():
            self.success_frame.place_forget()

        ttk.Button(c, text="💾 Save PDF", command=save_pdf, style="Accent.TButton", width=20).pack(pady=5)
        ttk.Button(c, text="📄 Save Text", command=save_txt, width=20).pack(pady=5)
        ttk.Button(c, text="Close", command=close, width=20).pack(pady=20)
