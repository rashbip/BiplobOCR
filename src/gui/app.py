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
        self.geometry("1280x850")
        self.minsize(1000, 700)
        
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
        # --- Main Layout (Sidebar + Content) ---
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill="both", expand=True)

        # 1. Sidebar (Left) - Fixed width
        self.sidebar = ttk.Frame(self.main_container, width=240, padding=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False) # Force width
        
        # Sidebar Header (Logo)
        self.sidebar_header = ttk.Frame(self.sidebar, padding=20)
        self.sidebar_header.pack(fill="x")
        ttk.Label(self.sidebar_header, text="📜 BiplobOCR", font=("Segoe UI Variable Display", 18, "bold"), foreground="#e04f5f").pack(anchor="w")
        ttk.Label(self.sidebar_header, text="v1.2.4 • Windows Edition", font=("Segoe UI", 8), foreground="gray").pack(anchor="w")

        # Sidebar Nav
        self.nav_frame = ttk.Frame(self.sidebar, padding=(10, 20))
        self.nav_frame.pack(fill="x", expand=True, anchor="n")
        
        self.btn_home = self.create_nav_btn("🏠 Home", "home")
        self.btn_tools = self.create_nav_btn("🛠 Tools", "scan")
        self.btn_batch = self.create_nav_btn("📂 Batch Process", "batch")
        self.btn_history = self.create_nav_btn("🕒 History", "history")

        # Sidebar Footer
        self.footer_frame = ttk.Frame(self.sidebar, padding=20)
        self.footer_frame.pack(side="bottom", fill="x")
        self.btn_settings = self.create_nav_btn("⚙️ Settings", "settings", parent=self.footer_frame)
        ttk.Label(self.footer_frame, text="Help & Support", foreground="gray", cursor="hand2").pack(anchor="w", pady=(10, 0))

        # Separator
        ttk.Separator(self.main_container, orient="vertical").pack(side="left", fill="y")

        # 2. Content Area (Right)
        self.content_area = ttk.Frame(self.main_container)
        self.content_area.pack(side="left", fill="both", expand=True)
        
        # --- VIEWS ---
        self.view_home = ttk.Frame(self.content_area, padding=40)
        self.view_scan = ttk.Frame(self.content_area) 
        self.view_settings = ttk.Frame(self.content_area, padding=40)
        self.view_history = ttk.Frame(self.content_area, padding=40)
        self.view_batch = ttk.Frame(self.content_area, padding=40) # Placeholder

        self.build_home_view()
        self.build_scan_view()
        self.build_settings_view()
        self.build_history_view()

        # Init
        self.switch_tab("home")
    
    def create_nav_btn(self, text, tab, parent=None):
        if not parent: parent = self.nav_frame
        btn = ttk.Button(parent, text=text, command=lambda: self.switch_tab(tab), style="TButton")
        btn.pack(fill="x", pady=2, anchor="w")
        return btn

    def switch_tab(self, tab):
        # Hide all
        for v in [self.view_home, self.view_scan, self.view_settings, self.view_history, self.view_batch]:
            v.pack_forget()
        
        # Reset NAV styles (simple toggle simulation)
        for b in [self.btn_home, self.btn_tools, self.btn_batch, self.btn_history, self.btn_settings]:
            b.state(['!pressed', '!disabled']) # Reset state if needed or style
            b.configure(style="TButton")

        if tab == "home":
            self.view_home.pack(fill="both", expand=True)
            self.btn_home.configure(style="Accent.TButton")
        elif tab == "scan":
            self.view_scan.pack(fill="both", expand=True)
            self.btn_tools.configure(style="Accent.TButton")
        elif tab == "batch":
            self.view_batch.pack(fill="both", expand=True)
            self.btn_batch.configure(style="Accent.TButton")
        elif tab == "history":
            self.view_history.pack(fill="both", expand=True)
            self.btn_history.configure(style="Accent.TButton")
        elif tab == "settings":
            self.view_settings.pack(fill="both", expand=True)
            self.btn_settings.configure(style="Accent.TButton")

    def build_home_view(self):
        # Header
        ttk.Label(self.view_home, text="Welcome to BiplobOCR", font=("Segoe UI Variable Display", 28, "bold")).pack(anchor="w")
        ttk.Label(self.view_home, text="Ready to digitize your documents? Start a new scan or pick up where you left off.", font=("Segoe UI", 12), foreground="gray").pack(anchor="w", pady=(5, 30))
        
        # Cards Container
        cards_frame = ttk.Frame(self.view_home)
        cards_frame.pack(fill="x", pady=20)
        
        # Card 1: Start New Task (The "Dashed" Box lookalike)
        card1 = ttk.Frame(cards_frame, style="Card.TFrame", padding=2)
        card1.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Inner content of Card 1
        c1_inner = ttk.Frame(card1, padding=30)
        c1_inner.pack(fill="both", expand=True)
        
        ttk.Label(c1_inner, text="⬆️", font=("Segoe UI", 24)).pack(pady=(0,10))
        ttk.Label(c1_inner, text="Start a new OCR task", font=("Segoe UI", 16, "bold")).pack()
        ttk.Label(c1_inner, text="Drag and drop PDF, JPG files here", foreground="gray").pack(pady=5)
        
        ttk.Button(c1_inner, text="Select from Computer", style="Accent.TButton", command=self.open_pdf_from_home).pack(pady=20, ipadx=10, ipady=5)
        
        # Card 2: Batch Process (Simpler)
        card2 = ttk.Frame(cards_frame, style="Card.TFrame", padding=2)
        card2.pack(side="left", fill="both", expand=True, padx=(10, 0))
        
        c2_inner = ttk.Frame(card2, padding=30)
        c2_inner.pack(fill="both", expand=True)
        
        ttk.Label(c2_inner, text="📑", font=("Segoe UI", 24)).pack(pady=(0,10))
        ttk.Label(c2_inner, text="Batch Process", font=("Segoe UI", 16, "bold")).pack()
        ttk.Label(c2_inner, text="Convert multiple files at once", foreground="gray").pack(pady=5)
        ttk.Button(c2_inner, text="Open Batch Tool", command=lambda: self.switch_tab("batch")).pack(pady=20)

        # Recent Documents Section
        ttk.Label(self.view_home, text="Recent Documents", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(40, 10))
        
        # Treeview for Table
        cols = ("Filename", "Date", "Size", "Status")
        self.tree = ttk.Treeview(self.view_home, columns=cols, show="headings", height=8)
        self.tree.pack(fill="both", expand=True)
        
        self.tree.heading("Filename", text="Filename")
        self.tree.heading("Date", text="Date")
        self.tree.heading("Size", text="Size")
        self.tree.heading("Status", text="Status")
        
        self.tree.column("Filename", width=300)
        self.tree.column("Date", width=150)
        self.tree.column("Size", width=100)
        self.tree.column("Status", width=100)
        
        # Dummy Data
        self.tree.insert("", "end", values=("Invoice_Q4_2023.pdf", "Today, 10:23 AM", "2.4 MB", "Completed"))
        self.tree.insert("", "end", values=("Scan_Contract_002.png", "Yesterday", "4.1 MB", "Processing"))
        self.tree.insert("", "end", values=("Meeting_Notes_Oct.pdf", "Oct 20, 2023", "0.8 MB", "Failed"))

    def build_history_view(self):
        ttk.Label(self.view_history, text="History Logs", font=("Segoe UI", 20, "bold")).pack(anchor="w", pady=20)
        ttk.Label(self.view_history, text="Shows past processing attempts.").pack(anchor="w")

    def open_pdf_from_home(self):
        self.switch_tab("scan")
        self.open_pdf()

    def build_scan_view(self):
        # Sidebar + Viewer Layout
        self.scan_paned = ttk.PanedWindow(self.view_scan, orient="horizontal")
        self.scan_paned.pack(fill="both", expand=True)

        # Sidebar
        self.scan_sidebar = ttk.Frame(self.scan_paned, width=300, padding=15)
        self.scan_paned.add(self.scan_sidebar, weight=0)
        
        # Header
        ttk.Label(self.scan_sidebar, text="Active Task", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 20))
        
        ttk.Button(self.scan_sidebar, text="📂 Open New PDF", command=self.open_pdf).pack(fill="x", pady=2)
        
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
        self.lbl_status = ttk.Label(self.scan_sidebar, text=app_state.t("lbl_status_idle"), foreground="gray", wraplength=250)
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
