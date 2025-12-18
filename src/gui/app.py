import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
import shutil
import time
import pikepdf
import os
import sys
import subprocess
import threading
import fitz  # PyMuPDF
from PIL import Image, ImageTk

# Local imports
from ..core.constants import APP_NAME, TEMP_DIR
from ..core.ocr_engine import detect_pdf_type, run_ocr, cancel_ocr
from ..core.config_manager import state as app_state
from ..core.history_manager import history
from .pdf_viewer import PDFViewer
from .settings_dialog import SettingsDialog
from ..core.theme import THEME_COLOR, THEME_COLOR_HOVER, THEME_COLOR_ACTIVE, BG_COLOR, SURFACE_COLOR, FG_COLOR
from .views.home_view import HomeView
from .views.batch_view import BatchView
from .views.history_view import HistoryView
from ..core import gpu_manager

class BiplobOCR(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        
        self.title(app_state.t("app_title"))
        self.geometry("1400x900") 
        self.minsize(1100, 750) # Increased to prevent clipping
        self.configure(bg=BG_COLOR)
        
        # Flags
        self.stop_processing_flag = False
        self.processing_active = False 

        # Hardware Info
        self.sys_info = gpu_manager.get_system_info()
        self.available_gpus = self.sys_info["gpus"]
        self.cpu_count = self.sys_info["cpu_count"]
        
        self.setup_custom_theme()
        
        self.current_pdf_path = None
        self.current_pdf_password = None
        
        self.build_ui()
        
        self.protocol("WM_DELETE_WINDOW", self.on_close_app)
        
        self.deiconify()

    def on_close_app(self):
        if self.processing_active:
            if messagebox.askyesno("Exit", "Processing in progress. Stop and exit?"):
                self.cancel_processing()
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
        
        self.btn_home = self.create_nav_btn(app_state.t("nav_home"), "home")
        self.btn_tools = self.create_nav_btn(app_state.t("nav_tools"), "scan")
        self.btn_batch = self.create_nav_btn(app_state.t("nav_batch"), "batch")
        self.btn_history = self.create_nav_btn(app_state.t("nav_history"), "history")

        self.footer_frame = ttk.Frame(self.sidebar, padding=20)
        self.footer_frame.pack(side="bottom", fill="x")
        self.btn_settings = self.create_nav_btn(app_state.t("nav_settings"), "settings", parent=self.footer_frame)
        ttk.Label(self.footer_frame, text=app_state.t("lbl_help"), foreground="gray", cursor="hand2").pack(anchor="w", pady=(10, 0))

        tk.Frame(self.main_container, bg="#333333", width=1).pack(side="left", fill="y")

        # 2. Right Panel (Content + Global Status Bar)
        self.right_panel = ttk.Frame(self.main_container)
        self.right_panel.pack(side="left", fill="both", expand=True)

        self.content_area = ttk.Frame(self.right_panel)
        self.content_area.pack(side="top", fill="both", expand=True)
        
        # --- GLOBAL STATUS BAR ---
        self.status_bar = ttk.Frame(self.right_panel, style="Card.TFrame", padding=10)
        
        self.lbl_global_status = ttk.Label(self.status_bar, text="Processing...", background=SURFACE_COLOR, font=("Segoe UI", 10, "bold"))
        self.lbl_global_status.pack(side="left", padx=10)
        
        self.global_progress = ttk.Progressbar(self.status_bar, mode="indeterminate", style="Horizontal.TProgressbar", length=300)
        self.global_progress.pack(side="left", fill="x", expand=True, padx=20)
        
        self.btn_cancel_global = ttk.Button(self.status_bar, text="🟥 STOP", command=self.cancel_processing, style="Danger.TButton")
        self.btn_cancel_global.pack(side="right", padx=10)

        # Vars (Initialize BEFORE views)
        self.var_deskew = tk.BooleanVar(value=app_state.get_option("deskew"))
        self.var_clean = tk.BooleanVar(value=app_state.get_option("clean"))
        self.var_rotate = tk.BooleanVar(value=app_state.get_option("rotate"))
        self.var_force = tk.BooleanVar(value=app_state.get_option("force"))
        self.var_optimize = tk.StringVar(value=app_state.get_option("optimize"))
        self.var_gpu = tk.BooleanVar(value=app_state.get_option("use_gpu"))
        self.var_gpu_device = tk.StringVar(value=app_state.get_option("gpu_device") or "Auto")
        self.var_cpu_threads = tk.IntVar(value=app_state.get_option("max_cpu_threads") or 2)
        self.var_lang = tk.StringVar(value=app_state.get("language", "en"))

        # --- VIEWS ---
        self.view_home = HomeView(self.content_area, self)
        self.view_batch = BatchView(self.content_area, self)
        self.view_history = HistoryView(self.content_area, self)

        self.view_scan = ttk.Frame(self.content_area) 
        self.view_settings = ttk.Frame(self.content_area, padding=40)

        self.build_scan_view()
        self.build_settings_view()

        self.view_home.pack(fill="both", expand=True)
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
            self.view_home.refresh_recent_docs() 
        elif tab == "scan":
            self.view_scan.pack(fill="both", expand=True)
            self.btn_tools.configure(style="Accent.TButton")
        elif tab == "batch":
            self.view_batch.pack(fill="both", expand=True)
            self.btn_batch.configure(style="Accent.TButton")
        elif tab == "history":
            self.view_history.pack(fill="both", expand=True)
            self.btn_history.configure(style="Accent.TButton")
            self.view_history.refresh()
        elif tab == "settings":
            self.view_settings.pack(fill="both", expand=True)
            self.btn_settings.configure(style="Accent.TButton")

    def show_global_status(self, msg, determinate=False):
        self.processing_active = True
        try:
            self.status_bar.pack(side="bottom", fill="x")
            self.lbl_global_status.config(text=msg)
            if determinate:
                self.global_progress.config(mode="determinate", value=0)
            else:
                self.global_progress.config(mode="indeterminate")
                self.global_progress.start(10)
        except: pass

    def hide_global_status(self):
        self.processing_active = False
        try:
            self.global_progress.stop()
        except: pass
        try:
            self.status_bar.pack_forget()
        except: pass

    def update_global_progress(self, val, max_val):
        try:
            self.global_progress.config(mode="determinate", maximum=max_val, value=val)
        except: pass

    def cancel_processing(self):
        self.stop_processing_flag = True
        cancel_ocr()
        try:
            self.lbl_global_status.config(text="Stopping...")
        except: pass

    def update_global_status_detail(self, val, page, total, start_time):
        try:
            # Monotonic progress check
            if not hasattr(self, 'max_page_seen'): self.max_page_seen = 0
            if page > self.max_page_seen: self.max_page_seen = page
            else: page = self.max_page_seen # Prevent backward jumps in UI
            
            # Recalculate val based on max_seen to keep bar smooth
            real_val = (page / total) * 100 if total else 0
            self.global_progress["value"] = real_val
            
            # ETR Calculation
            elapsed = time.time() - start_time
            if page > 0:
                avg_sec_per_page = elapsed / page
                remaining_pages = total - page
                etr_seconds = int(remaining_pages * avg_sec_per_page)
                
                # Format ETR
                if etr_seconds > 3600:
                    etr_str = f"{etr_seconds//3600}h {(etr_seconds%3600)//60}m"
                else:
                    etr_str = f"{etr_seconds//60}m {etr_seconds%60}s"
                
                txt = f"Processing Page {page} of {total} ({int(real_val)}%) - ETR: {etr_str}"
            else:
                txt = f"Processing Page {page} of {total} ({int(real_val)}%)"

            self.lbl_global_status.config(text=txt)
        except: pass

    # --- SINGLE SCAN ---
    def start_processing_thread(self): 
        self.save_settings_inline() 
        self.max_page_seen = 0  # Reset counter
        
        # PRE-CHECK: Detect potential issues before starting
        if not self.var_force.get() and self.current_pdf_path:
            # We check if file has text
            pdf_type = detect_pdf_type(self.current_pdf_path)
            if pdf_type in ['text', 'mixed']:
                msg = app_state.t("msg_text_detected") if app_state.get("language") == "en" else "File contains text."
                msg += "\n\n" + ("Enable 'Force OCR' to re-process?" if app_state.get("language") == "en" else "Force OCR enabled?")
                
                # Ask: Yes = Force, No = Cancel or Proceed?
                # User wants "ask at first... if ok continue". 
                if messagebox.askyesno("Text Detected", msg):
                    self.var_force.set(True)
                else:
                    # If they say No, we proceed with force=False (Skip Text mode)
                    # But if they meant "Cancel", they should hit Stop or we should offer Cancel.
                    # Standard logic: No means "Don't force", so we try standard (skip/mix).
                    pass

        self.btn_process.config(state="disabled")
        self.stop_processing_flag = False
        self.show_global_status(app_state.t("lbl_status_processing"))
        
        thread = threading.Thread(target=self.run_process_logic)
        thread.daemon = True
        thread.start()

    def run_process_logic(self):
        try:
            start_time = time.time()
            if self.stop_processing_flag: raise Exception("Process Cancelled")
            
            # Gather selected languages
            selected_langs = []
            if hasattr(self, 'scan_lang_vars'):
                for lang, var in self.scan_lang_vars.items():
                    if var.get(): selected_langs.append(lang)
            
            # Default fallback if somehow empty (though UI should prevent or we prevent here)
            if not selected_langs:
                 raise Exception("No OCR language selected! Please select at least one data pack.")

            # Save selection for next time
            app_state.set_option("last_used_ocr_languages", selected_langs)
            app_state.save_config({}) # Persist to disk
            
            ocr_lang = "+".join(selected_langs)
            
            opts = {
                "deskew": self.var_deskew.get(),
                "clean": self.var_clean.get(),
                "rotate": self.var_rotate.get(),
                "optimize": self.var_optimize.get(),
                "use_gpu": self.var_gpu.get(),
                "gpu_device": self.var_gpu_device.get(),
                "max_cpu_threads": self.var_cpu_threads.get(),
                "language": ocr_lang
            }
            temp_out = os.path.join(TEMP_DIR, "processed_output.pdf")
            
            total_pages = 0
            try:
                if self.viewer and self.viewer.pdf_path == self.current_pdf_path:
                    total_pages = self.viewer.total_pages
                else:
                    with fitz.open(self.current_pdf_path) as doc:
                        total_pages = len(doc)
            except: total_pages = 1

            def update_prog(p):
                if total_pages > 0:
                    val = (p / total_pages) * 100
                    self.after(0, lambda v=val, p=p, t=total_pages: self.update_global_status_detail(v, p, t, start_time))
            
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
            # Check if this error was actually due to a manual stop
            if self.stop_processing_flag:
                self.after(0, lambda: self.on_process_cancelled())
                return

            err_msg = str(e.stderr) if e.stderr else str(e)
            # Truncate overly long error logs
            if len(err_msg) > 800:
                err_msg = "...(logs truncated)...\n" + err_msg[-800:]
                
            self.after(0, lambda: self.on_process_fail(err_msg))
            
        except Exception as e:
            err_msg = str(e)
            if "Process Cancelled" in err_msg or self.stop_processing_flag:
                self.after(0, lambda: self.on_process_cancelled())
            else:
                self.after(0, lambda: self.on_process_fail(err_msg))

    def on_process_cancelled(self):
        self.hide_global_status()
        self.btn_process.config(state="normal")
        self.lbl_status.config(text="Cancelled")
        fname = os.path.basename(self.current_pdf_path) if self.current_pdf_path else "Unknown"
        history.add_entry(fname, "Cancelled", source_path=self.current_pdf_path)
    
    def on_process_fail(self, msg):
        self.hide_global_status()
        self.btn_process.config(state="normal")
        self.lbl_status.config(text="Failed.")
        fname = os.path.basename(self.current_pdf_path) if self.current_pdf_path else "Unknown"
        history.add_entry(fname, "Failed", source_path=self.current_pdf_path)
        messagebox.showerror("Error", msg)

    def on_process_success(self, temp_out, sidecar):
        self.hide_global_status()
        self.btn_process.config(state="normal")
        self.lbl_status.config(text=app_state.t("lbl_status_done"))
        fname = os.path.basename(self.current_pdf_path)
        size_mb = os.path.getsize(temp_out) / (1024*1024)
        history.add_entry(fname, "Completed", f"{size_mb:.1f} MB", source_path=self.current_pdf_path, output_path=temp_out)
        self.show_success_ui(temp_out, sidecar)

    # --- BATCH ---
    def start_batch_processing(self):
        if not hasattr(self, 'batch_files') or not self.batch_files:
            messagebox.showwarning("Empty", "Please add files to process.")
            return
            
        out_dir = filedialog.askdirectory(title="Select Output Folder")
        if not out_dir: return
        
        self.save_settings_inline()

        self.btn_start_batch.config(state="disabled")
        self.stop_processing_flag = False
        
        self.show_global_status("Batch Processing Started...", determinate=True)
        self.update_global_progress(0, len(self.batch_files) * 100) 
        
        threading.Thread(target=self.run_batch_logic, args=(out_dir,), daemon=True).start()

    def add_batch_files(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
        if not files: return
        if not hasattr(self, 'batch_files'): self.batch_files = []
        for f in files:
            if any(bf["path"] == f for bf in self.batch_files): continue
            item_id = self.batch_tree.insert("", "end", values=(os.path.basename(f), "Pending"))
            self.batch_files.append({"path": f, "id": item_id, "status": "Pending"})

    def clear_batch_files(self):
        self.batch_tree.delete(*self.batch_tree.get_children())
        self.batch_files = []

    def run_batch_logic(self, out_dir):
        print("Starting batch logic...")
        selected_langs = []
        if hasattr(self, 'batch_lang_vars'):
            for lang, var in self.batch_lang_vars.items():
                if var.get(): selected_langs.append(lang)
        
        print(f"Batch languages: {selected_langs}")

        if not selected_langs:
            print("No languages selected!")
            self.after(0, lambda: messagebox.showerror("Error", "No OCR languages selected for batch!"))
            self.after(0, lambda: self.on_batch_complete(0, len(self.batch_files))) 
            return

        # Save selection
        # Note: calling app_state methods is generally thread-safe for simple dicts, but save_config writes file.
        # Ideally should be main thread, but doing it here is likely fine or we can schedule it.
        try:
             app_state.set_option("last_used_ocr_languages", selected_langs)
             app_state.save_config({})
        except Exception as e: print(f"Config save error: {e}")

        ocr_lang = "+".join(selected_langs)
        print(f"OCR Lang string: {ocr_lang}")

        opts = {
            "language": ocr_lang,
            "deskew": self.var_deskew.get(),
            "clean": self.var_clean.get(),
            "rotate": self.var_rotate.get(),
            "optimize": self.var_optimize.get(),
            "use_gpu": self.var_gpu.get(),
            "gpu_device": self.var_gpu_device.get(),
            "max_cpu_threads": self.var_cpu_threads.get()
        }
        
        success_count = 0
        total_docs = len(self.batch_files)
        
        for i, item in enumerate(self.batch_files):
            if self.stop_processing_flag: break
            fpath = item["path"]
            item_id = item["id"]
            fname = os.path.basename(fpath)
            
            self.after(0, lambda id=item_id: self.batch_tree.set(id, "Status", "Processing..."))
            self.batch_max_seen_page = 0 # Reset per file
            
            try:
                out_name = f"biplob_ocr_{fname}"
                out_path = os.path.join(out_dir, out_name)
                
                doc_total_pages = 1
                try:
                    with fitz.open(fpath) as d: doc_total_pages = len(d)
                except: pass
                
                # File Start Time
                file_start_time = time.time()

                def batch_prog_cb(p):
                    if doc_total_pages > 0:
                        doc_pct = (p / doc_total_pages) * 100
                        global_val = (i * 100) + doc_pct
                        
                        # ETR Logic (Current File)
                        elapsed = time.time() - file_start_time
                        avg_p = elapsed / p if p > 0 else 0
                        rem_p = doc_total_pages - p
                        etr = int(rem_p * avg_p)
                        etr_str = f"{etr//60}m {etr%60}s"
                        
                        self.after(0, lambda v=global_val, p=p, t=doc_total_pages, n=fname, idx=i+1, e=etr_str: 
                            self.update_batch_status_detail(v, idx, total_docs, n, p, t, e))

                pw = None
                try: 
                    with pikepdf.open(fpath): pass
                except: 
                    raise Exception("Password Required")

                run_ocr(fpath, out_path, None, force=True, options=opts, progress_callback=batch_prog_cb)
                
                if self.stop_processing_flag: raise Exception("Process Cancelled")
                     
                self.after(0, lambda id=item_id: self.batch_tree.set(id, "Status", "✅ Done"))
                history.add_entry(fname, "Batch Success", "N/A", source_path=fpath, output_path=out_path)
                success_count += 1
                
            except Exception as e:
                status = "❌ Failed"
                err_msg = str(e)
                if "Process Cancelled" in err_msg or self.stop_processing_flag:
                    status = "⛔ Cancelled"
                    self.after(0, lambda id=item_id: self.batch_tree.set(id, "Status", status))
                    history.add_entry(fname, "Batch Cancelled", source_path=fpath)
                    break 
                self.after(0, lambda id=item_id: self.batch_tree.set(id, "Status", status))
                history.add_entry(fname, "Batch Failed", source_path=fpath)
            
            self.after(0, lambda v=(i+1)*100: self.global_progress.configure(value=v))
        
        self.after(0, lambda: self.on_batch_complete(success_count, total_docs))

    def update_batch_status_detail(self, val, idx, total_docs, fname, page, total_pages, etr_str):
        if not hasattr(self, 'batch_max_seen_page'): self.batch_max_seen_page = 0
        if page > self.batch_max_seen_page: self.batch_max_seen_page = page
        else: page = self.batch_max_seen_page

        self.global_progress.configure(maximum=total_docs*100, value=val)
        self.lbl_global_status.config(text=f"[{idx}/{total_docs}] {fname}: Page {page}/{total_pages} ({int((page/total_pages)*100)}%) - ETR: {etr_str}")

    def on_batch_complete(self, success, total):
        self.hide_global_status()
        self.btn_start_batch.config(state="normal")
        if self.stop_processing_flag:
            messagebox.showinfo("Batch Stopped", f"Processing Stopped.\nSuccessful: {success}")
        else:
            messagebox.showinfo("Batch Complete", f"Processed {total} files.\nSuccessful: {success}")

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
        
        # Options
        opt_frame = ttk.LabelFrame(self.scan_sidebar, text=app_state.t("grp_options"), padding=10)
        opt_frame.pack(fill="x", pady=10)
        ttk.Checkbutton(opt_frame, text=app_state.t("opt_deskew"), variable=self.var_deskew).pack(anchor="w", pady=2)
        ttk.Checkbutton(opt_frame, text=app_state.t("opt_clean"), variable=self.var_clean).pack(anchor="w", pady=2)
        ttk.Checkbutton(opt_frame, text=app_state.t("opt_rotate"), variable=self.var_rotate).pack(anchor="w", pady=2)
        ttk.Checkbutton(opt_frame, text=app_state.t("opt_force"), variable=self.var_force).pack(anchor="w", pady=2)
        ttk.Label(opt_frame, text=app_state.t("lbl_optimize")).pack(anchor="w", pady=(10, 2))
        ttk.Combobox(opt_frame, textvariable=self.var_optimize, values=["0", "1", "2", "3"], state="readonly").pack(fill="x")

        # Multi-Select Languages
        lang_frame = ttk.LabelFrame(self.scan_sidebar, text="Processing Languages", padding=10)
        lang_frame.pack(fill="x", pady=10) # Removed expand=True to keep it compact
        
        # Load available and previously selected
        from ..core.ocr_engine import get_available_languages
        avail = get_available_languages()
        
        # Filter internal packs from Scan view availability
        internal_packs = app_state.get("internal_packs", [])
        avail = [l for l in avail if l not in internal_packs]

        last_used = app_state.get("last_used_ocr_languages")
        if not last_used: last_used = [app_state.get("ocr_language", "eng")]
        
        # Scrollable container for langs with FIXED HEIGHT
        lc = tk.Canvas(lang_frame, bg=SURFACE_COLOR, highlightthickness=0, height=120) 
        ls = ttk.Scrollbar(lang_frame, orient="vertical", command=lc.yview)
        lf = ttk.Frame(lc, style="Card.TFrame")
        
        lf.bind("<Configure>", lambda e: lc.configure(scrollregion=lc.bbox("all")))
        lc.create_window((0, 0), window=lf, anchor="nw")
        lc.configure(yscrollcommand=ls.set)
        
        lc.pack(side="left", fill="x", expand=True) # Fill width
        ls.pack(side="right", fill="y")
        
        self.scan_lang_vars = {}
        for l in avail:
            var = tk.BooleanVar(value=(l in last_used))
            btn = ttk.Checkbutton(lf, text=l, variable=var)
            btn.pack(anchor="w")
            self.scan_lang_vars[l] = var

        self.btn_process = ttk.Button(self.scan_sidebar, text=app_state.t("btn_process"), command=self.start_processing_thread, state="disabled", style="Accent.TButton")
        self.btn_process.pack(fill="x", pady=20)
        self.lbl_status = ttk.Label(self.scan_sidebar, text=app_state.t("lbl_status_idle"), foreground="gray", wraplength=250)
        self.lbl_status.pack(anchor="w", pady=5)
        self.viewer_container = ttk.Frame(self.scan_paned)
        self.scan_paned.add(self.viewer_container, weight=1)
        self.viewer = PDFViewer(self.viewer_container)
        self.viewer.pack(fill="both", expand=True)
        self.success_frame = ttk.Frame(self.viewer_container, style="Card.TFrame", padding=20)

    def build_settings_view(self):
        # Create Scrollable Container
        canvas = tk.Canvas(self.view_settings, bg=BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.view_settings, orient="vertical", command=canvas.yview)
        self.settings_scroll_frame = ttk.Frame(canvas)
        
        self.settings_scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        window_id = canvas.create_window((0, 0), window=self.settings_scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Ensure full width
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(window_id, width=e.width))
        
        # Enable Mousewheel Scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # Bind mousewheel to canvas and all descendants (recursively if needed, but binding to canvas + frame is usually enough if they have focus or pointer is over them)
        # However, for simplicity in Tkinter, binding to the canvas and ensuring it catches events is key.
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Build UI into settings_scroll_frame
        lbl = ttk.Label(self.settings_scroll_frame, text=app_state.t("settings_title"), font=("Segoe UI", 20, "bold"))
        lbl.pack(anchor="w", pady=(0, 20))
        
        # Hardware Config
        f_hw = ttk.LabelFrame(self.settings_scroll_frame, text=app_state.t("lbl_hw_settings"), padding=20)
        f_hw.pack(fill="x", pady=10)
        
        # GPU Selection
        ttk.Label(f_hw, text=app_state.t("lbl_dev_select")).pack(anchor="w")
        gpu_vals = ["Auto"] + self.available_gpus
        cb_gpu = ttk.Combobox(f_hw, textvariable=self.var_gpu_device, values=gpu_vals, state="readonly")
        cb_gpu.pack(fill="x", pady=(5, 10))
        
        ttk.Checkbutton(f_hw, text=app_state.t("lbl_gpu"), variable=self.var_gpu).pack(anchor="w")
        
        # Threads
        ttk.Label(f_hw, text=f"{app_state.t('lbl_threads')} (Total Cores: {self.cpu_count})").pack(anchor="w", pady=(10,0))
        ttk.Label(f_hw, text="Lower this value if your PC freezes.", foreground="gray", font=("Segoe UI", 8)).pack(anchor="w")
        
        # Scale for threads
        s_threads = tk.Scale(f_hw, from_=1, to=self.cpu_count, orient="horizontal", variable=self.var_cpu_threads, background=SURFACE_COLOR, foreground=FG_COLOR, highlightthickness=0)
        s_threads.pack(fill="x", pady=5)
        
        # Lang
        f_lang = ttk.LabelFrame(self.settings_scroll_frame, text=app_state.t("lbl_lang"), padding=20)
        f_lang.pack(fill="x", pady=10)
        
        # 1. Interface Language
        ttk.Label(f_lang, text=app_state.t("lbl_lang")).pack(anchor="w")
        self.cb_lang = ttk.Combobox(f_lang, textvariable=self.var_lang, values=["en", "bn"], state="readonly")
        self.cb_lang.pack(fill="x", pady=(5, 15))
        
        # 2. OCR Language
        from ..core.ocr_engine import get_available_languages
        self.avail_langs = get_available_languages()
        
        ttk.Label(f_lang, text=app_state.t("lbl_ocr_lang")).pack(anchor="w")
        self.var_ocr_lang = tk.StringVar(value=app_state.get("ocr_language", "eng")) # Need to ensure init somewhere or just here
        
        self.cb_ocr_lang = ttk.Combobox(f_lang, textvariable=self.var_ocr_lang, values=self.avail_langs, state="readonly")
        self.cb_ocr_lang.pack(fill="x", pady=5)
        
        # Data Packs Management
        ttk.Label(f_lang, text="Installed Data Packs", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(15, 5))
        
        # Scrollable Container for Packs
        pack_container = ttk.Frame(f_lang, style="Card.TFrame", padding=2)
        pack_container.pack(fill="x", ipady=5)
        
        self.packs_canvas = tk.Canvas(pack_container, bg=BG_COLOR, height=150, highlightthickness=0)
        self.packs_scrollbar = ttk.Scrollbar(pack_container, orient="vertical", command=self.packs_canvas.yview)
        self.packs_scroll_frame = ttk.Frame(self.packs_canvas, style="Card.TFrame")
        
        self.packs_scroll_frame.bind("<Configure>", lambda e: self.packs_canvas.configure(scrollregion=self.packs_canvas.bbox("all")))
        self.packs_window = self.packs_canvas.create_window((0, 0), window=self.packs_scroll_frame, anchor="nw")
        self.packs_canvas.configure(yscrollcommand=self.packs_scrollbar.set)
        
        self.packs_canvas.pack(side="left", fill="both", expand=True)
        self.packs_scrollbar.pack(side="right", fill="y")
        self.packs_canvas.bind('<Configure>', lambda e: self.packs_canvas.itemconfig(self.packs_window, width=e.width))

        btn_add_pack = ttk.Button(f_lang, text="➕ Add Data Pack", command=self.add_data_pack)
        btn_add_pack.pack(anchor="e", pady=5)
        
        self.refresh_data_packs_ui()
        
        # Save Trigger
        self.cb_lang.bind("<<ComboboxSelected>>", lambda e: self.save_settings_inline())
        self.cb_ocr_lang.bind("<<ComboboxSelected>>", lambda e: self.save_settings_inline())
        cb_gpu.bind("<<ComboboxSelected>>", lambda e: self.save_settings_inline())
        s_threads.bind("<ButtonRelease-1>", lambda e: self.save_settings_inline())
        
        # Danger Zone
        ttk.Separator(self.settings_scroll_frame, orient="horizontal").pack(fill="x", pady=30)
        
        f_danger = ttk.LabelFrame(self.settings_scroll_frame, text="Danger Zone", padding=20)
        f_danger.pack(fill="x", pady=(0, 20))
        
        ttk.Label(f_danger, text="Reset application to factory defaults. This cannot be undone.", foreground="#ff5555").pack(anchor="w")
        ttk.Button(f_danger, text="⚠ Factory Reset", style="Danger.TButton", command=self.factory_reset).pack(anchor="w", pady=(10, 0))

    def factory_reset(self):
        print("Factory reset triggered") # Debug
        if messagebox.askyesno("Factory Reset", "Are you sure you want to reset all settings and data?"):
            try:
                if os.path.exists("config.json"): os.remove("config.json")
                if os.path.exists("history.json"): os.remove("history.json")
                if os.path.exists("history.json"): os.remove("history.json") # Duplicate check? Safe
                
                messagebox.showinfo("Reset Complete", "Application will now restart.")
                self.restart_application(force=True)
                
            except Exception as e:
                messagebox.showerror("Error", f"Reset failed: {e}")

    def refresh_data_packs_ui(self):
        for w in self.packs_scroll_frame.winfo_children(): w.destroy()
        
        from ..core.ocr_engine import get_tessdata_dir
        d = get_tessdata_dir()
        if not os.path.exists(d): return
        
        files = sorted([f for f in os.listdir(d) if "traineddata" in f])
        
        for f in files:
            is_disabled = f.endswith(".disabled")
            clean_name = f.replace(".disabled", "")
            
            row = ttk.Frame(self.packs_scroll_frame, padding=5)
            row.pack(fill="x", pady=1)
            
            # Icon/Name/Status
            icon = "🔴" if is_disabled else "🟢"
            
            # Check if internal
            internal_list = app_state.get("internal_packs", [])
            is_internal = clean_name in internal_list
            
            display_text = f"{icon} {clean_name}"
            if is_internal: display_text += " (Internal)"
            
            lbl = ttk.Label(row, text=display_text, font=("Segoe UI", 9))
            if is_disabled: lbl.config(foreground="gray")
            elif is_internal: lbl.config(foreground="orange")
            lbl.pack(side="left", padx=5)
            
            # Context Menu Logic
            def show_context_menu(event, name=clean_name, internal=is_internal):
                menu = tk.Menu(self, tearoff=0)
                if internal:
                    menu.add_command(label="Mark as External (Public)", command=lambda: toggle_internal(name, False))
                else:
                    menu.add_command(label="Mark as Internal (Hidden)", command=lambda: toggle_internal(name, True))
                menu.tk_popup(event.x_root, event.y_root)
            
            def toggle_internal(name, make_internal):
                current = app_state.get("internal_packs", [])
                if make_internal:
                    if name not in current: current.append(name)
                else:
                    if name in current: current.remove(name)
                
                app_state.set_option("internal_packs", current)
                app_state.save_config({})
                self.refresh_data_packs_ui() # Refresh UI
                
                # Update language lists elsewhere? Technically they will update on next view rebuild,
                # but might need immediate refresh if user goes back to scan.
                # Ideally, we should trigger a reload of available langs.
                # For now, simplistic refresh of settings UI is enough feedback.

            # Bind right click
            lbl.bind("<Button-3>", show_context_menu)
            row.bind("<Button-3>", show_context_menu)

            # Actions
            if clean_name == "osd.traineddata":
                ttk.Label(row, text="(System)", font=("Segoe UI", 8), foreground="gray").pack(side="right", padx=10)
                # OSD can still be marked internal/external via right click, but cannot be deleted/disabled.
                # If user wants to "mark internal" they can.
            else:
                def toggle_disable(fname=f, disabled=is_disabled):
                    src = os.path.join(d, fname)
                    if disabled:
                        dst = os.path.join(d, fname.replace(".disabled", ""))
                    else:
                        dst = os.path.join(d, fname + ".disabled")
                    try:
                        os.rename(src, dst)
                        self.refresh_data_packs_ui()
                        # Refresh lang list
                        from ..core.ocr_engine import get_available_languages
                        self.avail_langs = get_available_languages()
                        # Re-filter internal logic for combobox?
                        # Settings combobox should probably show ALL (or follow same rules? usually all to select default)
                        # We'll leave combobox showing all for now or update it.
                        self.cb_ocr_lang['values'] = self.avail_langs
                        if self.var_ocr_lang.get() not in self.avail_langs: self.var_ocr_lang.set(self.avail_langs[0] if self.avail_langs else "eng")
    
                    except Exception as e:
                        messagebox.showerror("Error", str(e))
    
                def delete_pack(fname=f):
                    if messagebox.askyesno("Confirm", f"Delete {fname}?"):
                        try:
                            os.remove(os.path.join(d, fname))
                            self.refresh_data_packs_ui()
                            from ..core.ocr_engine import get_available_languages
                            self.avail_langs = get_available_languages()
                            self.cb_ocr_lang['values'] = self.avail_langs
                            if self.var_ocr_lang.get() not in self.avail_langs: self.var_ocr_lang.set(self.avail_langs[0] if self.avail_langs else "eng")
                        except Exception as e:
                            messagebox.showerror("Error", str(e))
    
                btn_del = ttk.Button(row, text="🗑", width=3, command=delete_pack, style="Danger.TButton")
                btn_del.pack(side="right", padx=2)
                
                btn_toggle = ttk.Button(row, text="Enable" if is_disabled else "Disable", width=8, command=toggle_disable)
                btn_toggle.pack(side="right", padx=2)

    def add_data_pack(self):
        from ..core.ocr_engine import get_tessdata_dir
        f = filedialog.askopenfilename(title="Select Tesseract Data File", filetypes=[("Trained Data", "*.traineddata")])
        if not f: return
        
        try:
            # Basic Validation: Check header
            with open(f, 'rb') as tf:
                header = tf.read(15)
                # Tesseract traineddata usually starts with specific bytes, but simply checking existence/size is safer initially without brittle magic checks.
                # Real check: just ensure it's not empty.
                if len(header) < 10: raise Exception("Invalid file content")
            
            dest = os.path.join(get_tessdata_dir(), os.path.basename(f))
            shutil.copy(f, dest)
            
            messagebox.showinfo("Success", f"Installed {os.path.basename(f)}")
            
            # Refresh Lists
            self.refresh_data_packs_ui()
            from ..core.ocr_engine import get_available_languages
            self.avail_langs = get_available_languages()
            self.cb_ocr_lang['values'] = self.avail_langs
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to install data pack: {e}")

    def restart_application(self, force=False):
        """Restart the application safely."""
        if not force:
            if not messagebox.askyesno("Restart", "The application needs to restart to apply changes.\n\nRestart now?"):
                return

        try:
            self.quit() # Stop mainloop
            self.destroy() # Destroy window
        except: pass
        
        # Relaunch
        try:
            subprocess.Popen([sys.executable] + sys.argv)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restart: {e}")
        finally:
            sys.exit()

    def save_settings_inline(self):
        old_lang = app_state.get("language")
        new_lang = self.var_lang.get()
        new_conf = { 
            "language": new_lang, 
            "ocr_language": self.var_ocr_lang.get(),
            "theme": "dark", 
            "use_gpu": self.var_gpu.get(),
            "gpu_device": self.var_gpu_device.get(),
            "max_cpu_threads": self.var_cpu_threads.get()
        }
        app_state.save_config(new_conf)
        
        if old_lang != new_lang: 
            self.restart_application()

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

    def open_dropped_pdf(self, file_path):
        # TkinterDnD might return paths in curly braces {file.pdf} if spaces exist
        file_path = file_path.strip('{}')
        if not file_path.lower().endswith('.pdf'):
            messagebox.showerror("Error", "Only PDF files are supported.")
            return

        self.current_pdf_path = file_path
        self.switch_tab("scan")
        
        password = None
        try: 
            with pikepdf.open(file_path): pass
        except pikepdf.PasswordError:
            password = simpledialog.askstring("Password", "Enter PDF Password:", show="*")
            if not password: return
        
        self.current_pdf_password = password
        self.viewer.load_pdf(file_path, password)
        self.btn_process.config(state="normal")
        self.lbl_status.config(text=f"Loaded: {os.path.basename(file_path)}")

    def add_dropped_batch_files(self, file_paths):
        # TkinterDnD passes a string of paths, potentially with braces
        # We need to parse this string carefully.
        # Simple split is risky if spaces are present, but DnD returns {path with space} path_no_space
        
        # Robust parsing of TkinterDnD file list
        if isinstance(file_paths, str):
            # If it's a single string like "{C:/A B/foo.pdf} C:/baz.pdf", we need to split it
            raw_paths = self.tk.splitlist(file_paths)
        else:
            raw_paths = file_paths
            
        if not hasattr(self, 'batch_files'): self.batch_files = []
        
        count = 0
        for f in raw_paths:
            if f.lower().endswith('.pdf'):
                if any(bf["path"] == f for bf in self.batch_files): continue
                item_id = self.batch_tree.insert("", "end", values=(os.path.basename(f), "Pending"))
                self.batch_files.append({"path": f, "id": item_id, "status": "Pending"})
                count += 1
        
        if count > 0:
            messagebox.showinfo("Files Added", f"Added {count} files to batch.")

    def show_success_ui(self, temp_out, sidecar):
        self.success_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        for c in self.success_frame.winfo_children(): c.destroy()
        c = ttk.Frame(self.success_frame, style="Card.TFrame")
        c.place(relx=0.5, rely=0.5, anchor="center")
        ttk.Label(c, text="✅ " + app_state.t("msg_success"), font=("Segoe UI", 24), background=SURFACE_COLOR).pack(pady=10)
        
        def save_pdf():
            f = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
            if f:
                try:
                    shutil.copy(temp_out, f)
                    messagebox.showinfo("Saved", "PDF Saved!")
                    # Update History with actual path
                    fname = os.path.basename(self.current_pdf_path)
                    history.update_output_path(fname, f)
                except Exception as e:
                    messagebox.showerror("Error", f"Save failed: {e}")
        def save_txt():
            f = filedialog.asksaveasfilename(defaultextension=".txt")
            if f:
                shutil.copy(sidecar, f)
                messagebox.showinfo("Saved", "Text Saved!")
        def close(): self.success_frame.place_forget()
        ttk.Button(c, text="💾 Save PDF", command=save_pdf, style="Accent.TButton", width=20).pack(pady=5)
        ttk.Button(c, text="📄 Save Text", command=save_txt, width=20).pack(pady=5)
        ttk.Button(c, text="Close", command=close, width=20).pack(pady=20)
