
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
from ..core.history_manager import history
from .pdf_viewer import PDFViewer
from .settings_dialog import SettingsDialog

# Company Theme - Strict adherence
THEME_COLOR = "#A50F0F"
THEME_COLOR_HOVER = "#c91212"
THEME_COLOR_ACTIVE = "#8a0c0c"
BG_COLOR = "#1e1e1e"
SURFACE_COLOR = "#2d2d2d"
FG_COLOR = "#ffffff"

class BiplobOCR(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        
        self.title(app_state.t("app_title"))
        self.geometry("1280x850")
        self.minsize(1000, 700)
        self.configure(bg=BG_COLOR)
        
        self.setup_custom_theme()
        
        self.current_pdf_path = None
        self.current_pdf_password = None
        
        self.build_ui()
        self.deiconify()

    def load_settings(self):
        # We handle theme manually now
        pass

    def setup_custom_theme(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except:
            style.theme_use("default")

        # Global Colors
        self.option_add("*background", BG_COLOR)
        self.option_add("*foreground", FG_COLOR)
        self.option_add("*selectBackground", THEME_COLOR)
        self.option_add("*selectForeground", "white")
        self.option_add("*Entry.fieldBackground", SURFACE_COLOR)
        self.option_add("*Listbox.background", SURFACE_COLOR)

        # -- TTK Styles --
        
        # General Defaults
        style.configure(".", 
            background=BG_COLOR, 
            foreground=FG_COLOR, 
            troughcolor=BG_COLOR,
            fieldbackground=SURFACE_COLOR,
            borderwidth=0,
            darkcolor=BG_COLOR,
            lightcolor=BG_COLOR,
            selectbackground=THEME_COLOR
        )

        # TFrame
        style.configure("TFrame", background=BG_COLOR)
        style.configure("Card.TFrame", background=SURFACE_COLOR, relief="flat")

        # TLabel
        style.configure("TLabel", background=BG_COLOR, foreground=FG_COLOR, font=("Segoe UI", 10))
        
        # Heading Labels
        style.configure("Header.TLabel", font=("Segoe UI Variable Display", 24, "bold"), foreground=THEME_COLOR)

        # TButton (Standard)
        style.configure("TButton", 
            background=SURFACE_COLOR, 
            foreground=FG_COLOR, 
            borderwidth=0, 
            padding=6,
            font=("Segoe UI", 10)
        )
        style.map("TButton", 
            background=[("active", "#3e3e3e"), ("pressed", "#4e4e4e")],
            foreground=[("active", "white")]
        )

        # Accent Button (The Primary Action)
        style.configure("Accent.TButton", 
            background=THEME_COLOR, 
            foreground="white",
            font=("Segoe UI", 10, "bold")
        )
        style.map("Accent.TButton", 
            background=[("active", THEME_COLOR_HOVER), ("pressed", THEME_COLOR_ACTIVE)]
        )

        # TEntry / Combobox
        style.configure("TEntry", fieldbackground=SURFACE_COLOR, foreground=FG_COLOR, padding=5)
        style.configure("TCombobox", fieldbackground=SURFACE_COLOR, background=SURFACE_COLOR, foreground=FG_COLOR, arrowcolor="white")
        style.map("TCombobox", fieldbackground=[("readonly", SURFACE_COLOR)], selectbackground=[("readonly", THEME_COLOR)])

        # Treeview
        style.configure("Treeview", 
            background=SURFACE_COLOR, 
            fieldbackground=SURFACE_COLOR, 
            foreground=FG_COLOR,
            borderwidth=0,
            rowheight=30,
            font=("Segoe UI", 10)
        )
        style.map("Treeview", background=[("selected", THEME_COLOR)], foreground=[("selected", "white")])
        
        style.configure("Treeview.Heading", 
            background=BG_COLOR, 
            foreground="gray", 
            font=("Segoe UI", 9, "bold"),
            relief="flat"
        )
        style.map("Treeview.Heading", background=[("active", BG_COLOR)])

        # Separator
        style.configure("TSeparator", background="#3e3e3e")

        # Checkbutton
        style.configure("TCheckbutton", background=BG_COLOR, foreground=FG_COLOR)
        style.map("TCheckbutton", background=[("active", BG_COLOR)], indicatorcolor=[("selected", THEME_COLOR)])

        # Labelframe
        style.configure("TLabelframe", background=BG_COLOR, foreground=FG_COLOR, bordercolor="#3e3e3e")
        style.configure("TLabelframe.Label", background=BG_COLOR, foreground=THEME_COLOR)

        # Scrollbar (Vertical)
        style.configure("Vertical.TScrollbar", 
            gripcount=0,
            background=SURFACE_COLOR,
            darkcolor=BG_COLOR,
            lightcolor=BG_COLOR,
            troughcolor=BG_COLOR,
            bordercolor=BG_COLOR,
            arrowcolor="white"
        )
        style.map("Vertical.TScrollbar", background=[("active", "#4e4e4e")])

    def build_ui(self):
        # --- Main Layout (Sidebar + Content) ---
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill="both", expand=True)

        # 1. Sidebar (Left)
        # Use a slightly different color or just BG_COLOR
        self.sidebar = ttk.Frame(self.main_container, width=240, style="TFrame")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False) 
        
        # Sidebar Header
        self.sidebar_header = ttk.Frame(self.sidebar, padding=20)
        self.sidebar_header.pack(fill="x")
        ttk.Label(self.sidebar_header, text="📜 BiplobOCR", style="Header.TLabel", font=("Segoe UI Variable Display", 18, "bold"), foreground=THEME_COLOR).pack(anchor="w")
        ttk.Label(self.sidebar_header, text="Version 2.2", font=("Segoe UI", 8), foreground="gray").pack(anchor="w")

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

        # Separator (Manual line for cleaner look)
        tk.Frame(self.main_container, bg="#333333", width=1).pack(side="left", fill="y")

        # 2. Content Area
        self.content_area = ttk.Frame(self.main_container)
        self.content_area.pack(side="left", fill="both", expand=True)
        
        # --- VIEWS ---
        self.view_home = ttk.Frame(self.content_area, padding=40)
        self.view_scan = ttk.Frame(self.content_area) 
        self.view_settings = ttk.Frame(self.content_area, padding=40)
        self.view_history = ttk.Frame(self.content_area, padding=40)
        self.view_batch = ttk.Frame(self.content_area, padding=40)

        self.build_home_view()
        self.build_scan_view()
        self.build_settings_view()
        self.build_history_view()
        self.build_batch_view()

        # Init
        self.switch_tab("home")
    
    def create_nav_btn(self, text, tab, parent=None):
        if not parent: parent = self.nav_frame
        btn = ttk.Button(parent, text=text, command=lambda: self.switch_tab(tab), style="TButton")
        btn.pack(fill="x", pady=2, anchor="w")
        return btn

    def switch_tab(self, tab):
        for v in [self.view_home, self.view_scan, self.view_settings, self.view_history, self.view_batch]:
            v.pack_forget()
        
        for b in [self.btn_home, self.btn_tools, self.btn_batch, self.btn_history, self.btn_settings]:
            b.state(['!pressed', '!disabled']) 
            b.configure(style="TButton")

        if tab == "home":
            self.view_home.pack(fill="both", expand=True)
            self.btn_home.configure(style="Accent.TButton")
            self.refresh_recent_docs() 
        elif tab == "scan":
            self.view_scan.pack(fill="both", expand=True)
            self.btn_tools.configure(style="Accent.TButton")
        elif tab == "batch":
            self.view_batch.pack(fill="both", expand=True)
            self.btn_batch.configure(style="Accent.TButton")
        elif tab == "history":
            self.view_history.pack(fill="both", expand=True)
            self.btn_history.configure(style="Accent.TButton")
            self.refresh_history_view()
        elif tab == "settings":
            self.view_settings.pack(fill="both", expand=True)
            self.btn_settings.configure(style="Accent.TButton")

    def build_home_view(self):
        ttk.Label(self.view_home, text="Welcome to BiplobOCR", style="Header.TLabel").pack(anchor="w")
        ttk.Label(self.view_home, text="Ready to digitize your documents? Start a new scan or pick up where you left off.", font=("Segoe UI", 12), foreground="gray").pack(anchor="w", pady=(5, 30))
        
        cards_frame = ttk.Frame(self.view_home)
        cards_frame.pack(fill="x", pady=20)
        
        # Start Card
        card1 = ttk.Frame(cards_frame, style="Card.TFrame", padding=2)
        card1.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Colorize border manually through framing if needed, but simple bg is ok
        c1_inner = ttk.Frame(card1, padding=30, style="Card.TFrame")
        c1_inner.pack(fill="both", expand=True)
        
        ttk.Label(c1_inner, text="📂", font=("Segoe UI", 32), background=SURFACE_COLOR).pack(pady=(0,10))
        ttk.Label(c1_inner, text="Start a new OCR task", font=("Segoe UI", 16, "bold"), background=SURFACE_COLOR).pack()
        ttk.Label(c1_inner, text="Securely process PDF, JPG, PNG", foreground="gray", background=SURFACE_COLOR).pack(pady=5)
        
        ttk.Button(c1_inner, text="Select from Computer", style="Accent.TButton", command=self.open_pdf_from_home).pack(pady=20, ipadx=10, ipady=5)
        
        # Batch Card
        card2 = ttk.Frame(cards_frame, style="Card.TFrame", padding=2)
        card2.pack(side="left", fill="both", expand=True, padx=(10, 0))
        
        c2_inner = ttk.Frame(card2, padding=30, style="Card.TFrame")
        c2_inner.pack(fill="both", expand=True)
        
        ttk.Label(c2_inner, text="📦", font=("Segoe UI", 32), background=SURFACE_COLOR).pack(pady=(0,10))
        ttk.Label(c2_inner, text="Batch Process", font=("Segoe UI", 16, "bold"), background=SURFACE_COLOR).pack()
        ttk.Button(c2_inner, text="Open Batch Tool", command=lambda: self.switch_tab("batch")).pack(pady=20)

        # Recent Documents (Home)
        ttk.Label(self.view_home, text="Recent Activity", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(40, 10))
        
        cols = ("Filename", "Date", "Status")
        self.tree_recent = ttk.Treeview(self.view_home, columns=cols, show="headings", height=6)
        self.tree_recent.pack(fill="both", expand=True)
        
        self.tree_recent.heading("Filename", text="Filename")
        self.tree_recent.heading("Date", text="Date")
        self.tree_recent.heading("Status", text="Status")
        
        self.tree_recent.column("Filename", width=300)
        self.tree_recent.column("Date", width=150)
        self.tree_recent.column("Status", width=100)
        
        self.refresh_recent_docs()

    def refresh_recent_docs(self):
        # Clear
        for item in self.tree_recent.get_children():
            self.tree_recent.delete(item)
        
        # Load from history
        data = history.get_all()
        for i, item in enumerate(data):
            if i >= 5: break # Only show top 5
            self.tree_recent.insert("", "end", values=(item["filename"], item["date"], item["status"]))

    def build_history_view(self):
        ttk.Label(self.view_history, text="History Logs", style="Header.TLabel").pack(anchor="w", pady=20)
        
        cols = ("Filename", "Date", "Size", "Status")
        self.tree_history = ttk.Treeview(self.view_history, columns=cols, show="headings")
        self.tree_history.pack(fill="both", expand=True)
        
        self.tree_history.heading("Filename", text="Filename")
        self.tree_history.heading("Date", text="Date")
        self.tree_history.heading("Size", text="Size")
        self.tree_history.heading("Status", text="Status")
        
        self.refresh_history_view()

    def refresh_history_view(self):
        for item in self.tree_history.get_children():
            self.tree_history.delete(item)
            
        data = history.get_all()
        for item in data:
            self.tree_history.insert("", "end", values=(item["filename"], item["date"], item["size"], item["status"]))

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
        ttk.Label(self.scan_sidebar, text="Active Task", font=("Segoe UI", 14, "bold"), foreground=THEME_COLOR).pack(anchor="w", pady=(0, 20))
        
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
        self.progress = ttk.Progressbar(self.scan_sidebar, mode="indeterminate", style="Horizontal.TProgressbar")
        self.progress.pack(fill="x")

        # Viewer Area
        self.viewer_container = ttk.Frame(self.scan_paned)
        self.scan_paned.add(self.viewer_container, weight=1)
        
        self.viewer = PDFViewer(self.viewer_container)
        self.viewer.pack(fill="both", expand=True)
        
        # Success Overlay (Initially Hidden)
        self.success_frame = ttk.Frame(self.viewer_container, style="Card.TFrame", padding=20)

    def build_batch_view(self):
        # Header
        ttk.Label(self.view_batch, text="Batch Processing", style="Header.TLabel").pack(anchor="w", pady=(20, 10))
        ttk.Label(self.view_batch, text="Process multiple documents automatically.", foreground="gray").pack(anchor="w", pady=(0, 20))

        # Toolbar
        toolbar = ttk.Frame(self.view_batch)
        toolbar.pack(fill="x", pady=5)
        
        ttk.Button(toolbar, text="➕ Add Files", command=self.add_batch_files, style="Accent.TButton", width=15).pack(side="left", padx=(0, 5))
        ttk.Button(toolbar, text="🗑 Clear List", command=self.clear_batch_files).pack(side="left")

        # File List (Treeview)
        cols = ("Filename", "Status")
        self.batch_tree = ttk.Treeview(self.view_batch, columns=cols, show="headings", height=10)
        self.batch_tree.pack(fill="both", expand=True, pady=10)
        
        self.batch_tree.heading("Filename", text="Filename")
        self.batch_tree.heading("Status", text="Status")
        
        self.batch_tree.column("Filename", width=400)
        self.batch_tree.column("Status", width=150)
        
        # Options & Actions
        controls = ttk.Frame(self.view_batch, padding=10, style="Card.TFrame")
        controls.pack(fill="x", pady=10)
        
        # Use existing vars
        opt_box = ttk.Frame(controls, style="Card.TFrame")
        opt_box.pack(side="left", fill="both", expand=True)
        ttk.Label(opt_box, text="Batch Options", font=("Segoe UI", 10, "bold"), background=SURFACE_COLOR).pack(anchor="w")
        
        ttk.Checkbutton(opt_box, text=app_state.t("opt_deskew"), variable=self.var_deskew).pack(side="left", padx=5)
        ttk.Checkbutton(opt_box, text=app_state.t("opt_clean"), variable=self.var_clean).pack(side="left", padx=5)
        
        self.btn_start_batch = ttk.Button(controls, text="▶ Start Batch", command=self.start_batch_processing, style="Accent.TButton", width=20)
        self.btn_start_batch.pack(side="right")
        
        # Batch Progress
        self.batch_progress = ttk.Progressbar(self.view_batch, mode="determinate", style="Horizontal.TProgressbar")
        self.batch_progress.pack(fill="x", pady=5)
        
        self.lbl_batch_status = ttk.Label(self.view_batch, text="Ready", foreground="gray")
        self.lbl_batch_status.pack(anchor="w")

        self.batch_files = [] # List of tuples/dicts: {"path": str, "id": str, "status": str}

    def add_batch_files(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
        if not files: return
        
        for f in files:
            # Check duplicates
            if any(bf["path"] == f for bf in self.batch_files): continue
            
            item_id = self.batch_tree.insert("", "end", values=(os.path.basename(f), "Pending"))
            self.batch_files.append({"path": f, "id": item_id, "status": "Pending"})
            
        self.lbl_batch_status.config(text=f"{len(self.batch_files)} documents added.")

    def clear_batch_files(self):
        self.batch_tree.delete(*self.batch_tree.get_children())
        self.batch_files = []
        self.lbl_batch_status.config(text="List cleared.")

    def start_batch_processing(self):
        if not self.batch_files:
            messagebox.showwarning("Empty", "Please add files to process.")
            return
            
        # Ask output directory
        out_dir = filedialog.askdirectory(title="Select Output Folder")
        if not out_dir: return
        
        self.btn_start_batch.config(state="disabled")
        self.batch_progress["value"] = 0
        self.batch_progress["maximum"] = len(self.batch_files)
        
        # Save config
        app_state.set_option("deskew", self.var_deskew.get())
        app_state.set_option("clean", self.var_clean.get())
        app_state.save_config({})

        threading.Thread(target=self.run_batch_logic, args=(out_dir,), daemon=True).start()

    def run_batch_logic(self, out_dir):
        opts = {
            "deskew": self.var_deskew.get(),
            "clean": self.var_clean.get(),
            "rotate": self.var_rotate.get(),
            "optimize": self.var_optimize.get(),
        }
        
        success_count = 0
        
        for i, item in enumerate(self.batch_files):
            fpath = item["path"]
            item_id = item["id"]
            fname = os.path.basename(fpath)
            
            # Update UI to "Processing"
            self.after(0, lambda id=item_id: self.batch_tree.set(id, "Status", "Processing..."))
            self.after(0, lambda v=i+1, f=fname: self.update_batch_ui_status(v, f))
            
            try:
                # Filename prefix logic
                out_name = f"biplob_ocr_{fname}"
                out_path = os.path.join(out_dir, out_name)
                
                # Check password (basic check, batch assumes no pass or skip)
                pw = None
                try: 
                    with pikepdf.open(fpath): pass
                except:
                    raise Exception("Password Required")

                run_ocr(fpath, out_path, pw, force=True, options=opts)
                
                # Success
                self.after(0, lambda id=item_id: self.batch_tree.set(id, "Status", "✅ Done"))
                history.add_entry(fname, "Batch Success", "N/A")
                success_count += 1
                
            except Exception as e:
                # Fail
                self.after(0, lambda id=item_id: self.batch_tree.set(id, "Status", "❌ Failed"))
                history.add_entry(fname, "Batch Failed")
                print(f"Batch Error on {fname}: {e}")
            
            self.after(0, lambda v=i+1: self.batch_progress.configure(value=v))
        
        self.after(0, lambda: self.on_batch_complete(success_count, len(self.batch_files)))

    def update_batch_ui_status(self, idx, fname):
        self.lbl_batch_status.config(text=f"Processing {idx}/{len(self.batch_files)}: {fname}")

    def on_batch_complete(self, success, total):
        self.btn_start_batch.config(state="normal")
        self.lbl_batch_status.config(text=f"Batch Run Completed. {success}/{total} successful.")
        messagebox.showinfo("Batch Complete", f"Processing Finished.\nSuccessful: {success}\nTotal: {total}")

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

        ttk.Label(self.view_settings, text="Changes require restart to fully apply UI text translations.", foreground="gray").pack(pady=20)
        
    def save_settings_inline(self):
        old_lang = app_state.get("language")
        new_lang = self.var_lang.get()
        
        new_conf = {
            "language": new_lang,
            "theme": "dark" # Enforce dark
        }
        app_state.save_config(new_conf)

        if old_lang != new_lang:
            messagebox.showinfo("Restart Required", "Applications language changed. Please restart BiplobOCR for changes to take effect.")

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
        self.lbl_status.config(text="Failed.")
        
        # Log failure
        fname = os.path.basename(self.current_pdf_path) if self.current_pdf_path else "Unknown"
        history.add_entry(fname, "Failed")
        
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
        
        # Log success
        fname = os.path.basename(self.current_pdf_path)
        # Get size
        size_mb = os.path.getsize(temp_out) / (1024*1024)
        history.add_entry(fname, "Completed", f"{size_mb:.1f} MB")
        
        self.show_success_ui(temp_out, sidecar)

    def show_success_ui(self, temp_out, sidecar):
        self.success_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        # Clear childs
        for c in self.success_frame.winfo_children(): c.destroy()
        
        # Center
        c = ttk.Frame(self.success_frame, style="Card.TFrame")
        c.place(relx=0.5, rely=0.5, anchor="center")
        
        ttk.Label(c, text="✅ " + app_state.t("msg_success"), font=("Segoe UI", 24), background=SURFACE_COLOR).pack(pady=10)
        
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
