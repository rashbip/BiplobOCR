"""
BiplobOCR - Main Application
Refactored for better maintainability. UI logic split into views and controllers.
"""
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinterdnd2 import TkinterDnD
import shutil
import os
import sys
import subprocess
import webbrowser
import pikepdf

# Local imports
from ..core.constants import APP_NAME
from ..core.config_manager import state as app_state
from ..core.history_manager import history
from ..core.theme import THEME_COLOR, BG_COLOR, SURFACE_COLOR
from ..core import gpu_manager

# Controllers
from .controllers.status_controller import StatusController
from .controllers.processing_controller import ProcessingController

# Widgets
from .widgets.theme_manager import setup_custom_theme

# Views
from .views.home_view import HomeView
from .views.batch_view import BatchView
from .views.history_view import HistoryView
from .views.scan_view import ScanView
from .views.settings_view import SettingsView


class BiplobOCR(TkinterDnD.Tk):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.withdraw()
        
        self.title(app_state.t("app_title"))
        self.geometry("1400x900") 
        self.minsize(1100, 750)
        self.configure(bg=BG_COLOR)
        
        # Flags
        self.stop_processing_flag = False
        self.processing_active = False 

        # Hardware Info
        self.sys_info = gpu_manager.get_system_info()
        self.available_gpus = self.sys_info["gpus"]
        self.cpu_count = self.sys_info["cpu_count"]
        
        # Apply theme
        setup_custom_theme(self)
        
        # PDF state
        self.current_pdf_path = None
        self.current_pdf_password = None
        
        # Initialize controllers
        self.status_controller = StatusController(self)
        self.processing_controller = ProcessingController(self)
        
        # Build UI
        self._init_variables()
        self.build_ui()
        
        self.protocol("WM_DELETE_WINDOW", self.on_close_app)
        
        self.deiconify()

    def _init_variables(self):
        """Initialize all tkinter variables."""
        self.var_deskew = tk.BooleanVar(value=app_state.get_option("deskew"))
        self.var_clean = tk.BooleanVar(value=app_state.get_option("clean"))
        self.var_rotate = tk.BooleanVar(value=app_state.get_option("rotate"))
        self.var_force = tk.BooleanVar(value=app_state.get_option("force"))
        self.var_optimize = tk.StringVar(value=app_state.get_option("optimize"))
        self.var_gpu = tk.BooleanVar(value=app_state.get_option("use_gpu"))
        self.var_gpu_device = tk.StringVar(value=app_state.get_option("gpu_device") or "Auto")
        self.var_cpu_threads = tk.IntVar(value=app_state.get_option("max_cpu_threads") or 2)
        self.var_lang = tk.StringVar(value=app_state.get("language", "en"))

    def on_close_app(self):
        """Handle application close."""
        if self.processing_active:
            if messagebox.askyesno("Exit", "Processing in progress. Stop and exit?"):
                self.processing_controller.cancel_processing()
                self.after(500, self.destroy)
        else:
            self.destroy()

    def build_ui(self):
        """Build the main UI layout."""
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill="both", expand=True)

        # 1. Sidebar (Left)
        self._build_sidebar()
        
        # Separator
        tk.Frame(self.main_container, bg="#333333", width=1).pack(side="left", fill="y")

        # 2. Right Panel (Content + Global Status Bar)
        self.right_panel = ttk.Frame(self.main_container)
        self.right_panel.pack(side="left", fill="both", expand=True)

        self.content_area = ttk.Frame(self.right_panel)
        self.content_area.pack(side="top", fill="both", expand=True)
        
        # Global Status Bar
        self._build_status_bar()
        
        # Initialize Views
        self._init_views()

    def _build_sidebar(self):
        """Build the sidebar navigation."""
        self.sidebar = ttk.Frame(self.main_container, width=240, style="TFrame")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False) 
        
        # Header
        self.sidebar_header = ttk.Frame(self.sidebar, padding=20)
        self.sidebar_header.pack(fill="x")
        ttk.Label(self.sidebar_header, text="📜 BiplobOCR", style="Header.TLabel", 
                  font=("Segoe UI Variable Display", 18, "bold"), foreground=THEME_COLOR).pack(anchor="w")
        ttk.Label(self.sidebar_header, text="Version 2.2", font=("Segoe UI", 8), 
                  foreground="gray").pack(anchor="w")

        # Navigation
        self.nav_frame = ttk.Frame(self.sidebar, padding=(10, 20))
        self.nav_frame.pack(fill="x", expand=True, anchor="n")
        
        self.btn_home = self._create_nav_btn(app_state.t("nav_home"), "home")
        self.btn_tools = self._create_nav_btn(app_state.t("nav_tools"), "scan")
        self.btn_batch = self._create_nav_btn(app_state.t("nav_batch"), "batch")
        self.btn_history = self._create_nav_btn(app_state.t("nav_history"), "history")

        # Footer
        self.footer_frame = ttk.Frame(self.sidebar, padding=20)
        self.footer_frame.pack(side="bottom", fill="x")
        self.btn_settings = self._create_nav_btn(app_state.t("nav_settings"), "settings", parent=self.footer_frame)
        self.lbl_help = ttk.Label(self.footer_frame, text=app_state.t("lbl_help"), foreground="gray", 
                  cursor="hand2")
        self.lbl_help.pack(anchor="w", pady=(10, 0))
        self.lbl_help.bind("<Button-1>", lambda e: self._open_help_url())

    def _build_status_bar(self):
        """Build the global status bar."""
        self.status_bar = ttk.Frame(self.right_panel, style="Card.TFrame", padding=10)
        
        self.lbl_global_status = ttk.Label(self.status_bar, text="Processing...", 
                                            background=SURFACE_COLOR, font=("Segoe UI", 10, "bold"))
        self.lbl_global_status.pack(side="left", padx=10)
        
        self.global_progress = ttk.Progressbar(self.status_bar, mode="indeterminate", 
                                                style="Horizontal.TProgressbar", length=300)
        self.global_progress.pack(side="left", fill="x", expand=True, padx=20)
        
        self.btn_cancel_global = ttk.Button(self.status_bar, text="🟥 STOP", 
                                             command=self.processing_controller.cancel_processing, 
                                             style="Danger.TButton")
        self.btn_cancel_global.pack(side="right", padx=10)
        
        self.btn_show_log = ttk.Button(self.status_bar, text="👁 See Process", 
                                        command=self.open_log_view, style="TButton")
        self.btn_show_log.pack(side="right", padx=5)

    def _init_views(self):
        """Initialize all views."""
        self.view_home = HomeView(self.content_area, self)
        self.view_batch = BatchView(self.content_area, self)
        self.view_history = HistoryView(self.content_area, self)
        self.view_scan = ScanView(self.content_area, self)
        self.view_settings = SettingsView(self.content_area, self)

        self.view_home.pack(fill="both", expand=True)
        self.switch_tab("home")
    
    def _create_nav_btn(self, text, tab, parent=None):
        """Create a navigation button."""
        if not parent:
            parent = self.nav_frame
        btn = ttk.Button(parent, text=text, command=lambda: self.switch_tab(tab), style="TButton")
        btn.pack(fill="x", pady=2, anchor="w")
        return btn

    def switch_tab(self, tab):
        """Switch between tabs/views."""
        views = [self.view_home, self.view_scan, self.view_settings, self.view_history, self.view_batch]
        buttons = [self.btn_home, self.btn_tools, self.btn_batch, self.btn_history, self.btn_settings]
        
        for v in views:
            v.pack_forget()
        for b in buttons:
            b.state(['!pressed', '!disabled']) 
            b.configure(style="TButton")

        if tab == "home":
            self.view_home.pack(fill="both", expand=True)
            self.btn_home.configure(style="Accent.TButton")
            self.view_home.refresh_recent_docs() 
        elif tab == "scan":
            self.view_scan.pack(fill="both", expand=True)
            self.btn_tools.configure(style="Accent.TButton")
            self.view_scan.refresh_languages()  # Refresh language list
        elif tab == "batch":
            self.view_batch.pack(fill="both", expand=True)
            self.btn_batch.configure(style="Accent.TButton")
            self.view_batch.refresh_languages()  # Refresh language list
        elif tab == "history":
            self.view_history.pack(fill="both", expand=True)
            self.btn_history.configure(style="Accent.TButton")
            self.view_history.refresh()
        elif tab == "settings":
            self.view_settings.pack(fill="both", expand=True)
            self.btn_settings.configure(style="Accent.TButton")

    def _open_help_url(self):
        """Open the help documentation URL in the default web browser."""
        webbrowser.open("https://rashidul.is-a.dev/BiplobOCRdocs/")

    # ==================== LOG VIEW ====================
    
    def open_log_view(self):
        """Open the log view window."""
        if hasattr(self, 'log_window') and self.log_window.winfo_exists():
            self.log_window.lift()
            return
            
        from .views.log_view import LogView
        self.log_window = LogView(self)
        self.log_window.protocol("WM_DELETE_WINDOW", self.close_log_view)

    def close_log_view(self):
        """Close the log view window."""
        if hasattr(self, 'log_window'):
            self.log_window.destroy()
            del self.log_window

    def log_bridge(self, msg):
        """Pass log messages to the log window if active."""
        if hasattr(self, 'log_window') and self.log_window.winfo_exists():
            self.after(0, lambda: self.log_window.append_log(msg))

    # ==================== FILE OPERATIONS ====================
    
    def open_pdf_from_home(self):
        """Open PDF from home view."""
        self.switch_tab("scan")
        self.open_pdf()

    def open_pdf(self):
        """Open a PDF file."""
        pdf = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not pdf:
            return
        self.current_pdf_path = pdf
        password = None
        try: 
            with pikepdf.open(pdf):
                pass
        except pikepdf.PasswordError:
            password = simpledialog.askstring("Password", "Enter PDF Password:", show="*")
            if not password:
                return
        self.current_pdf_password = password
        self.viewer.load_pdf(pdf, password)
        self.btn_process.config(state="normal")
        self.success_frame.place_forget()
        self.lbl_status.config(text=f"Loaded: {os.path.basename(pdf)}")

    def open_dropped_pdf(self, file_path):
        """Open a dropped PDF file."""
        file_path = file_path.strip('{}')
        if not file_path.lower().endswith('.pdf'):
            messagebox.showerror("Error", "Only PDF files are supported.")
            return

        self.current_pdf_path = file_path
        self.switch_tab("scan")
        
        password = None
        try: 
            with pikepdf.open(file_path):
                pass
        except pikepdf.PasswordError:
            password = simpledialog.askstring("Password", "Enter PDF Password:", show="*")
            if not password:
                return
        
        self.current_pdf_password = password
        self.viewer.load_pdf(file_path, password)
        self.btn_process.config(state="normal")
        self.lbl_status.config(text=f"Loaded: {os.path.basename(file_path)}")

    def add_dropped_batch_files(self, file_paths):
        """Add dropped files to batch queue."""
        if isinstance(file_paths, str):
            raw_paths = self.tk.splitlist(file_paths)
        else:
            raw_paths = file_paths
            
        if not hasattr(self, 'batch_files'):
            self.batch_files = []
        
        count = 0
        for f in raw_paths:
            if f.lower().endswith('.pdf'):
                if any(bf["path"] == f for bf in self.batch_files):
                    continue
                item_id = self.batch_tree.insert("", "end", values=(os.path.basename(f), "Pending"))
                self.batch_files.append({"path": f, "id": item_id, "status": "Pending"})
                count += 1
        
        if count > 0:
            messagebox.showinfo("Files Added", f"Added {count} files to batch.")

    # ==================== SUCCESS UI ====================

    def show_success_ui(self, temp_out, sidecar):
        """Show the success UI after processing."""
        self.success_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        for c in self.success_frame.winfo_children():
            c.destroy()
        
        c = ttk.Frame(self.success_frame, style="Card.TFrame")
        c.place(relx=0.5, rely=0.5, anchor="center")
        ttk.Label(c, text="✅ " + app_state.t("msg_success"), font=("Segoe UI", 24), 
                  background=SURFACE_COLOR).pack(pady=10)
        
        def save_pdf():
            f = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
            if f:
                try:
                    shutil.copy(temp_out, f)
                    messagebox.showinfo("Saved", "PDF Saved!")
                    fname = os.path.basename(self.current_pdf_path)
                    history.update_output_path(fname, f)
                except Exception as e:
                    messagebox.showerror("Error", f"Save failed: {e}")
        
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

    # ==================== SETTINGS ====================

    def save_settings_inline(self):
        """Save current settings."""
        old_lang = app_state.get("language")
        new_lang = self.var_lang.get()
        new_conf = { 
            "language": new_lang, 
            "ocr_language": self.var_ocr_lang.get() if hasattr(self, 'var_ocr_lang') else "eng",
            "theme": "dark", 
            "use_gpu": self.var_gpu.get(),
            "gpu_device": self.var_gpu_device.get(),
            "max_cpu_threads": self.var_cpu_threads.get()
        }
        app_state.save_config(new_conf)
        
        if old_lang != new_lang: 
            self.restart_application()

    def restart_application(self, force=False):
        """Restart the application safely."""
        if not force:
            if not messagebox.askyesno("Restart", 
                "The application needs to restart to apply changes.\n\nRestart now?"):
                return

        try:
            self.quit()
            self.destroy()
        except:
            pass
        
        try:
            subprocess.Popen([sys.executable] + sys.argv)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restart: {e}")
        finally:
            sys.exit()

    # ==================== BATCH OPERATIONS (delegated to controller) ====================
    
    def start_batch_processing(self):
        """Start batch processing."""
        self.processing_controller.start_batch_processing()

    def add_batch_files(self):
        """Add files to batch."""
        self.processing_controller.add_batch_files()

    def clear_batch_files(self):
        """Clear batch files."""
        self.processing_controller.clear_batch_files()
