
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
from ..core.ocr_engine import detect_pdf_type, run_ocr, run_tesseract_export, cancel_ocr
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
        self.geometry("1350x850") # Slightly wider for status bar
        self.minsize(1000, 700)
        self.configure(bg=BG_COLOR)
        
        # Flags
        self.stop_processing_flag = False
        self.processing_active = False # To check on exit

        self.setup_custom_theme()
        
        self.current_pdf_path = None
        self.current_pdf_password = None
        
        self.build_ui()
        
        # Bind Close Event
        self.protocol("WM_DELETE_WINDOW", self.on_close_app)
        
        self.deiconify()

    def on_close_app(self):
        if self.processing_active:
            if messagebox.askyesno("Exit", "Processing in progress. Stop and exit?"):
                self.cancel_processing()
                # Give it a moment to kill
                self.after(500, self.destroy)
        else:
            self.destroy()

    def load_settings(self):
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
        style.configure(".", background=BG_COLOR, foreground=FG_COLOR, troughcolor=BG_COLOR, fieldbackground=SURFACE_COLOR, borderwidth=0, darkcolor=BG_COLOR, lightcolor=BG_COLOR, selectbackground=THEME_COLOR)
        
        style.configure("TFrame", background=BG_COLOR)
        style.configure("Card.TFrame", background=SURFACE_COLOR, relief="flat")
        
        style.configure("TLabel", background=BG_COLOR, foreground=FG_COLOR, font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI Variable Display", 24, "bold"), foreground=THEME_COLOR)
        
        style.configure("TButton", background=SURFACE_COLOR, foreground=FG_COLOR, borderwidth=0, padding=6, font=("Segoe UI", 10))
        style.map("TButton", background=[("active", "#3e3e3e"), ("pressed", "#4e4e4e")], foreground=[("active", "white")])
        
        style.configure("Accent.TButton", background=THEME_COLOR, foreground="white", font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", THEME_COLOR_HOVER), ("pressed", THEME_COLOR_ACTIVE)])
        
        style.configure("Danger.TButton", background="#800000", foreground="white", font=("Segoe UI", 10, "bold"))
        style.map("Danger.TButton", background=[("active", "#5a0000")])
        
        style.configure("TEntry", fieldbackground=SURFACE_COLOR, foreground=FG_COLOR, padding=5)
        style.configure("TCombobox", fieldbackground=SURFACE_COLOR, background=SURFACE_COLOR, foreground=FG_COLOR, arrowcolor="white")
        style.map("TCombobox", fieldbackground=[("readonly", SURFACE_COLOR)], selectbackground=[("readonly", THEME_COLOR)])
        
        style.configure("Treeview", background=SURFACE_COLOR, fieldbackground=SURFACE_COLOR, foreground=FG_COLOR, borderwidth=0, rowheight=30, font=("Segoe UI", 10))
        style.map("Treeview", background=[("selected", THEME_COLOR)], foreground=[("selected", "white")])
        style.configure("Treeview.Heading", background=BG_COLOR, foreground="gray", font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Treeview.Heading", background=[("active", BG_COLOR)])
        
        style.configure("TSeparator", background="#3e3e3e")
        style.configure("TCheckbutton", background=BG_COLOR, foreground=FG_COLOR)
        style.map("TCheckbutton", background=[("active", BG_COLOR)], indicatorcolor=[("selected", THEME_COLOR)])
        
        style.configure("TLabelframe", background=BG_COLOR, foreground=FG_COLOR, bordercolor="#3e3e3e")
        style.configure("TLabelframe.Label", background=BG_COLOR, foreground=THEME_COLOR)
        
        style.configure("Vertical.TScrollbar", gripcount=0, background=SURFACE_COLOR, darkcolor=BG_COLOR, lightcolor=BG_COLOR, troughcolor=BG_COLOR, bordercolor=BG_COLOR, arrowcolor="white")
        style.map("Vertical.TScrollbar", background=[("active", "#4e4e4e")])
        
        style.configure("Horizontal.TProgressbar", background=THEME_COLOR, troughcolor=SURFACE_COLOR, bordercolor=SURFACE_COLOR, lightcolor=THEME_COLOR, darkcolor=THEME_COLOR)

    def build_ui(self):
        # --- Main Layout ---
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill="both", expand=True)

        # 1. Sidebar (Left)
        self.sidebar = ttk.Frame(self.main_container, width=240, style="TFrame")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False) 
        
        self.sidebar_header = ttk.Frame(self.sidebar, padding=20)
        self.sidebar_header.pack(fill="x")
        ttk.Label(self.sidebar_header, text="📜 BiplobOCR", style="Header.TLabel", font=("Segoe UI Variable Display", 18, "bold"), foreground=THEME_COLOR).pack(anchor="w")
        ttk.Label(self.sidebar_header, text="Version 2.2", font=("Segoe UI", 8), foreground="gray").pack(anchor="w")

        self.nav_frame = ttk.Frame(self.sidebar, padding=(10, 20))
        self.nav_frame.pack(fill="x", expand=True, anchor="n")
        
        self.btn_home = self.create_nav_btn("🏠 Home", "home")
        self.btn_tools = self.create_nav_btn("🛠 Tools", "scan")
        self.btn_batch = self.create_nav_btn("📂 Batch Process", "batch")
        self.btn_history = self.create_nav_btn("🕒 History", "history")

        self.footer_frame = ttk.Frame(self.sidebar, padding=20)
        self.footer_frame.pack(side="bottom", fill="x")
        self.btn_settings = self.create_nav_btn("⚙️ Settings", "settings", parent=self.footer_frame)
        ttk.Label(self.footer_frame, text="Help & Support", foreground="gray", cursor="hand2").pack(anchor="w", pady=(10, 0))

        tk.Frame(self.main_container, bg="#333333", width=1).pack(side="left", fill="y")

        # 2. Right Panel (Content + Global Status Bar)
        self.right_panel = ttk.Frame(self.main_container)
        self.right_panel.pack(side="left", fill="both", expand=True)

        # Content Area
        self.content_area = ttk.Frame(self.right_panel)
        self.content_area.pack(side="top", fill="both", expand=True)
        
        # --- GLOBAL STATUS BAR ---
        # Starts hidden
        self.status_bar = ttk.Frame(self.right_panel, style="Card.TFrame", padding=10)
        
        self.lbl_global_status = ttk.Label(self.status_bar, text="Processing...", background=SURFACE_COLOR, font=("Segoe UI", 10, "bold"))
        self.lbl_global_status.pack(side="left", padx=10)
        
        self.global_progress = ttk.Progressbar(self.status_bar, mode="indeterminate", style="Horizontal.TProgressbar", length=300)
        self.global_progress.pack(side="left", fill="x", expand=True, padx=20)
        
        self.btn_cancel_global = ttk.Button(self.status_bar, text="🟥 STOP", command=self.cancel_processing, style="Danger.TButton")
        self.btn_cancel_global.pack(side="right", padx=10)

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

    # --- PROCESS CONTROL & STATUS ---
    def show_global_status(self, msg, determinate=False):
        self.processing_active = True
        self.status_bar.pack(side="bottom", fill="x") # Show at bottom
        self.lbl_global_status.config(text=msg)
        if determinate:
            self.global_progress.config(mode="determinate", value=0)
        else:
            self.global_progress.config(mode="indeterminate")
            self.global_progress.start(10)

    def hide_global_status(self):
        self.processing_active = False
        self.global_progress.stop()
        self.status_bar.pack_forget()

    def update_global_progress(self, val, max_val):
        self.global_progress.config(mode="determinate", maximum=max_val, value=val)

    def cancel_processing(self):
        self.stop_processing_flag = True
        cancel_ocr() # Helper to kill subprocess
        self.lbl_global_status.config(text="Stopping...")

    # --- SINGLE SCAN LOGIC ---
    def start_processing_thread(self): 
        # Save options
        app_state.set_option("deskew", self.var_deskew.get())
        app_state.set_option("clean", self.var_clean.get())
        app_state.set_option("rotate", self.var_rotate.get())
        app_state.set_option("force", self.var_force.get())
        app_state.set_option("optimize", self.var_optimize.get())
        app_state.save_config({}) 

        self.btn_process.config(state="disabled")
        
        self.stop_processing_flag = False
        self.show_global_status(app_state.t("lbl_status_processing"))
        
        thread = threading.Thread(target=self.run_process_logic)
        thread.daemon = True
        thread.start()

    def run_process_logic(self):
        try:
            if self.stop_processing_flag: raise Exception("Process Cancelled")
            
            opts = {
                "deskew": self.var_deskew.get(),
                "clean": self.var_clean.get(),
                "rotate": self.var_rotate.get(),
                "optimize": self.var_optimize.get(),
            }
            temp_out = os.path.join(TEMP_DIR, "processed_output.pdf")
            
            # Determine total pages for progress
            total_pages = 0
            try:
                if self.viewer and self.viewer.pdf_path == self.current_pdf_path:
                    total_pages = self.viewer.total_pages
                else:
                    with fitz.open(self.current_pdf_path) as doc:
                        total_pages = len(doc)
            except:
                total_pages = 1 # Fallback

            def update_prog(p):
                # p is current page number
                if total_pages > 0:
                    val = (p / total_pages) * 100
                    self.after(0, lambda v=val, p=p, t=total_pages: self.update_global_status_detail(v, p, t))
            
            # Set determinate mode
            self.after(0, lambda: self.global_progress.config(mode="determinate", maximum=100, value=0))
            
            sidecar = run_ocr(
                self.current_pdf_path, 
                temp_out, 
                self.current_pdf_password, 
                self.var_force.get(),
                options=opts,
                progress_callback=update_prog
            )
            
            if self.stop_processing_flag: raise Exception("Process Cancelled")
            self.after(0, lambda: self.on_process_success(temp_out, sidecar))
            
        except subprocess.CalledProcessError as e:
            err_text = str(e.stderr).lower() if e.stderr else ""
            if "priorocrfounderror" in err_text or "page already has text" in err_text:
                self.after(0, lambda: self.ask_force_continuation())
            else:
                err_msg = str(e.stderr)
                self.after(0, lambda: self.on_process_fail(err_msg))
        except Exception as e:
            err_msg = str(e)
            if "Process Cancelled" in err_msg:
                self.after(0, lambda: self.on_process_cancelled())
            else:
                self.after(0, lambda: self.on_process_fail(err_msg))

    def update_global_status_detail(self, val, page, total):
        self.global_progress["value"] = val
        self.lbl_global_status.config(text=f"Processing Page {page} of {total} ({int(val)}%)")

    def on_process_cancelled(self):
        self.hide_global_status()
        self.btn_process.config(state="normal")
        self.lbl_status.config(text="Cancelled")
        fname = os.path.basename(self.current_pdf_path) if self.current_pdf_path else "Unknown"
        history.add_entry(fname, "Cancelled")
    
    def on_process_fail(self, msg):
        self.hide_global_status()
        self.btn_process.config(state="normal")
        self.lbl_status.config(text="Failed.")
        fname = os.path.basename(self.current_pdf_path) if self.current_pdf_path else "Unknown"
        history.add_entry(fname, "Failed")
        messagebox.showerror("Error", msg)

    def on_process_success(self, temp_out, sidecar):
        self.hide_global_status()
        self.btn_process.config(state="normal")
        self.lbl_status.config(text=app_state.t("lbl_status_done"))
        fname = os.path.basename(self.current_pdf_path)
        size_mb = os.path.getsize(temp_out) / (1024*1024)
        history.add_entry(fname, "Completed", f"{size_mb:.1f} MB")
        self.show_success_ui(temp_out, sidecar)

    # --- BATCH LOGIC ---
    def start_batch_processing(self):
        if not self.batch_files:
            messagebox.showwarning("Empty", "Please add files to process.")
            return
            
        out_dir = filedialog.askdirectory(title="Select Output Folder")
        if not out_dir: return
        
        self.btn_start_batch.config(state="disabled")
        self.stop_processing_flag = False
        
        self.show_global_status("Batch Processing Started...", determinate=True)
        self.update_global_progress(0, len(self.batch_files) * 100) # Max = total docs * 100%
        
        threading.Thread(target=self.run_batch_logic, args=(out_dir,), daemon=True).start()

    def run_batch_logic(self, out_dir):
        opts = {
            "deskew": self.var_deskew.get(),
            "clean": self.var_clean.get(),
            "rotate": self.var_rotate.get(),
            "optimize": self.var_optimize.get(),
        }
        
        success_count = 0
        total_docs = len(self.batch_files)
        
        for i, item in enumerate(self.batch_files):
            # Check Cancel
            if self.stop_processing_flag:
                break
                
            fpath = item["path"]
            item_id = item["id"]
            fname = os.path.basename(fpath)
            
            self.after(0, lambda id=item_id: self.batch_tree.set(id, "Status", "Processing..."))
            
            try:
                out_name = f"biplob_ocr_{fname}"
                out_path = os.path.join(out_dir, out_name)
                
                # Get total pages for this doc
                doc_total_pages = 1
                try:
                    with fitz.open(fpath) as d: doc_total_pages = len(d)
                except: pass
                
                def batch_prog_cb(p):
                    # Global progress:
                    # Completed docs * 100 + current doc %
                    if doc_total_pages > 0:
                        doc_pct = (p / doc_total_pages) * 100
                        global_val = (i * 100) + doc_pct
                        
                        self.after(0, lambda v=global_val, p=p, t=doc_total_pages, n=fname, idx=i+1: 
                            self.update_batch_status_detail(v, idx, total_docs, n, p, t))

                pw = None
                try: 
                    with pikepdf.open(fpath): pass
                except:
                    # Basic password check failed, maybe ask? 
                    # For batch, just fail
                    raise Exception("Password Required")

                run_ocr(fpath, out_path, None, force=True, options=opts, progress_callback=batch_prog_cb)
                
                if self.stop_processing_flag:
                     raise Exception("Process Cancelled")
                     
                self.after(0, lambda id=item_id: self.batch_tree.set(id, "Status", "✅ Done"))
                history.add_entry(fname, "Batch Success", "N/A")
                success_count += 1
                
            except Exception as e:
                status = "❌ Failed"
                err_msg = str(e)
                if "Process Cancelled" in err_msg or self.stop_processing_flag:
                    status = "⛔ Cancelled"
                    self.after(0, lambda id=item_id: self.batch_tree.set(id, "Status", status))
                    history.add_entry(fname, "Batch Cancelled")
                    break 
                
                self.after(0, lambda id=item_id: self.batch_tree.set(id, "Status", status))
                history.add_entry(fname, "Batch Failed")
            
            # After each doc, update global to (i+1)*100
            self.after(0, lambda v=(i+1)*100: self.global_progress.configure(value=v))
        
        self.after(0, lambda: self.on_batch_complete(success_count, total_docs))

    def update_batch_status_detail(self, val, idx, total_docs, fname, page, total_pages):
        # Update progressbar (max should be total_docs * 100)
        self.global_progress.configure(maximum=total_docs*100, value=val)
        self.lbl_global_status.config(text=f"[{idx}/{total_docs}] {fname}: Page {page}/{total_pages} ({int((page/total_pages)*100)}%)")

    def on_batch_complete(self, success, total):
        self.hide_global_status()
        self.btn_start_batch.config(state="normal")
        if self.stop_processing_flag:
            messagebox.showinfo("Batch Stopped", f"Processing Stopped.\nSuccessful: {success}")
        else:
            messagebox.showinfo("Batch Complete", f"Processed {total} files.\nSuccessful: {success}")

    # UI Builders
    def build_home_view(self):
        ttk.Label(self.view_home, text="Welcome to BiplobOCR", style="Header.TLabel").pack(anchor="w")
        ttk.Label(self.view_home, text="Ready to digitize your documents? Start a new scan or pick up where you left off.", font=("Segoe UI", 12), foreground="gray").pack(anchor="w", pady=(5, 30))
        
        cards_frame = ttk.Frame(self.view_home)
        cards_frame.pack(fill="x", pady=20)
        
        # Start Card
        card1 = ttk.Frame(cards_frame, style="Card.TFrame", padding=2)
        card1.pack(side="left", fill="both", expand=True, padx=(0, 10))
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
        for item in self.tree_recent.get_children(): self.tree_recent.delete(item)
        data = history.get_all()
        for i, item in enumerate(data):
            if i >= 5: break
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
        for item in self.tree_history.get_children(): self.tree_history.delete(item)
        data = history.get_all()
        for item in data: self.tree_history.insert("", "end", values=(item["filename"], item["date"], item["size"], item["status"]))

    def open_pdf_from_home(self):
        self.switch_tab("scan")
        self.open_pdf()

    def build_scan_view(self):
        self.scan_paned = ttk.PanedWindow(self.view_scan, orient="horizontal")
        self.scan_paned.pack(fill="both", expand=True)

        self.scan_sidebar = ttk.Frame(self.scan_paned, width=300, padding=15)
        self.scan_paned.add(self.scan_sidebar, weight=0)
        
        ttk.Label(self.scan_sidebar, text="Active Task", font=("Segoe UI", 14, "bold"), foreground=THEME_COLOR).pack(anchor="w", pady=(0, 20))
        ttk.Button(self.scan_sidebar, text="📂 Open New PDF", command=self.open_pdf).pack(fill="x", pady=2)
        
        opt_frame = ttk.LabelFrame(self.scan_sidebar, text=app_state.t("grp_options"), padding=10)
        opt_frame.pack(fill="x", pady=20)

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
        
        self.lbl_status = ttk.Label(self.scan_sidebar, text=app_state.t("lbl_status_idle"), foreground="gray", wraplength=250)
        self.lbl_status.pack(anchor="w", pady=5)
        # We removed local progress because global progress exists now, but keeping it as a small indicator or removing?
        # User requested: "progress should be present in evry screens bottom"
        # So we can remove this local one or keep it. I'll remove it to avoid redundancy and cleaner UI.

        self.viewer_container = ttk.Frame(self.scan_paned)
        self.scan_paned.add(self.viewer_container, weight=1)
        self.viewer = PDFViewer(self.viewer_container)
        self.viewer.pack(fill="both", expand=True)
        self.success_frame = ttk.Frame(self.viewer_container, style="Card.TFrame", padding=20)

    def build_batch_view(self):
        ttk.Label(self.view_batch, text="Batch Processing", style="Header.TLabel").pack(anchor="w", pady=(20, 10))
        ttk.Label(self.view_batch, text="Process multiple documents automatically.", foreground="gray").pack(anchor="w", pady=(0, 20))
        toolbar = ttk.Frame(self.view_batch)
        toolbar.pack(fill="x", pady=5)
        ttk.Button(toolbar, text="➕ Add Files", command=self.add_batch_files, style="Accent.TButton", width=15).pack(side="left", padx=(0, 5))
        ttk.Button(toolbar, text="🗑 Clear List", command=self.clear_batch_files).pack(side="left")

        cols = ("Filename", "Status")
        self.batch_tree = ttk.Treeview(self.view_batch, columns=cols, show="headings", height=10)
        self.batch_tree.pack(fill="both", expand=True, pady=10)
        self.batch_tree.heading("Filename", text="Filename")
        self.batch_tree.heading("Status", text="Status")
        self.batch_tree.column("Filename", width=400)
        self.batch_tree.column("Status", width=150)
        
        controls = ttk.Frame(self.view_batch, padding=10, style="Card.TFrame")
        controls.pack(fill="x", pady=10)
        
        opt_box = ttk.Frame(controls, style="Card.TFrame")
        opt_box.pack(side="left", fill="both", expand=True)
        ttk.Label(opt_box, text="Batch Options", font=("Segoe UI", 10, "bold"), background=SURFACE_COLOR).pack(anchor="w")
        ttk.Checkbutton(opt_box, text=app_state.t("opt_deskew"), variable=self.var_deskew).pack(side="left", padx=5)
        ttk.Checkbutton(opt_box, text=app_state.t("opt_clean"), variable=self.var_clean).pack(side="left", padx=5)
        
        self.btn_start_batch = ttk.Button(controls, text="▶ Start Batch", command=self.start_batch_processing, style="Accent.TButton", width=20)
        self.btn_start_batch.pack(side="right")
        
        self.batch_files = [] 

    def add_batch_files(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
        if not files: return
        for f in files:
            if any(bf["path"] == f for bf in self.batch_files): continue
            item_id = self.batch_tree.insert("", "end", values=(os.path.basename(f), "Pending"))
            self.batch_files.append({"path": f, "id": item_id, "status": "Pending"})

    def clear_batch_files(self):
        self.batch_tree.delete(*self.batch_tree.get_children())
        self.batch_files = []

    def build_settings_view(self):
        lbl = ttk.Label(self.view_settings, text=app_state.t("settings_title"), font=("Segoe UI", 20, "bold"))
        lbl.pack(anchor="w", pady=(0, 20))
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
        new_conf = { "language": new_lang, "theme": "dark" }
        app_state.save_config(new_conf)
        if old_lang != new_lang: messagebox.showinfo("Restart Required", "Applications language changed. Please restart BiplobOCR for changes to take effect.")

    # --- Actions ---
    def open_pdf(self):
        pdf = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not pdf: return
        self.current_pdf_path = pdf
        password = None
        try:
            with pikepdf.open(pdf): pass
        except pikepdf.PasswordError:
            password = simpledialog.askstring("Password", "Enter PDF Password:", show="*")
            if not password: return
        
        self.current_pdf_password = password
        self.viewer.load_pdf(pdf, password)
        self.btn_process.config(state="normal")
        self.success_frame.place_forget()
        self.lbl_status.config(text=f"Loaded: {os.path.basename(pdf)}")

    def ask_force_continuation(self):
        proceed = messagebox.askyesno("Text Detected", "Files already has text. Force OCR?")
        if proceed:
            self.var_force.set(True)
            self.start_processing_thread()
        else:
            self.on_process_fail("Aborted.")

    def show_success_ui(self, temp_out, sidecar):
        self.success_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        for c in self.success_frame.winfo_children(): c.destroy()
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
