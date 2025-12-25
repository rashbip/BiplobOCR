"""
Processing Controller - Handles single file and batch OCR processing logic.
Extracted from app.py for better maintainability.
"""
import os
import time
import threading
import subprocess
import fitz  # PyMuPDF
import pikepdf
from tkinter import filedialog, messagebox

from ...core.constants import TEMP_DIR
from ...core.ocr_engine import detect_pdf_type, run_ocr, cancel_ocr
from ...core.config_manager import state as app_state
from ...core.history_manager import history


class ProcessingController:
    """Handles all OCR processing logic for single and batch operations."""
    
    def __init__(self, app):
        self.app = app
        self.stop_flag = False
    
    def cancel_processing(self):
        """Cancel the current processing operation."""
        self.stop_flag = True
        cancel_ocr()
        try:
            self.app.lbl_global_status.config(text="Stopping...")
        except: 
            pass

    # ==================== SINGLE FILE PROCESSING ====================
    
    def start_processing_thread(self):
        """Start the single file OCR processing in a background thread."""
        self.app.save_settings_inline()
        self.app.status_controller.reset_page_counter()
        
        # PRE-CHECK: Detect potential issues before starting
        if not self.app.var_force.get() and self.app.current_pdf_path:
            pdf_type = detect_pdf_type(self.app.current_pdf_path)
            if pdf_type in ['text', 'mixed']:
                msg = app_state.t("msg_text_detected") if app_state.get("language") == "en" else "File contains text."
                msg += "\n\n" + ("Enable 'Force OCR' to re-process?" if app_state.get("language") == "en" else "Force OCR enabled?")
                
                if messagebox.askyesno("Text Detected", msg):
                    self.app.var_force.set(True)

        self.app.btn_process.config(state="disabled")
        self.stop_flag = False
        
        # Determine if we can show determinate progress immediately
        determinate = False
        if self.app.viewer and self.app.viewer.pdf_path == self.app.current_pdf_path:
            determinate = True
            
        self.app.status_controller.show_global_status(app_state.t("lbl_status_processing"), determinate=determinate)
        
        thread = threading.Thread(target=self._run_process_logic)
        thread.daemon = True
        thread.start()

    def _run_process_logic(self):
        """Internal: Run the OCR processing logic."""
        try:
            start_time = time.time()
            if self.stop_flag:
                raise Exception("Process Cancelled")
            
            # Gather selected languages
            selected_langs = []
            if hasattr(self.app, 'scan_lang_vars'):
                for lang, var in self.app.scan_lang_vars.items():
                    if var.get():
                        selected_langs.append(lang)
            
            if not selected_langs:
                raise Exception("No OCR language selected! Please select at least one data pack.")

            # Save selection for next time
            app_state.set_option("last_used_ocr_languages", selected_langs)
            app_state.save_config({})
            
            ocr_lang = "+".join(selected_langs)
            
            # Safe DPI parsing
            try:
                current_dpi = int(self.app.var_dpi.get())
            except:
                current_dpi = 300

            opts = {
                "deskew": self.app.var_deskew.get(),
                "clean": self.app.var_clean.get(),
                "rotate": self.app.var_rotate.get(),
                "optimize": self.app.var_optimize.get(),
                "use_gpu": self.app.var_gpu.get(),
                "gpu_device": self.app.var_gpu_device.get(),
                "max_cpu_threads": self.app.var_cpu_threads.get(),
                "rasterize": self.app.var_rasterize.get(),
                "dpi": current_dpi,
                "language": ocr_lang
            }
            temp_out = os.path.join(TEMP_DIR, "processed_output.pdf")
            
            total_pages = 0
            try:
                if self.app.viewer and self.app.viewer.pdf_path == self.app.current_pdf_path:
                    total_pages = self.app.viewer.total_pages
                else:
                    with fitz.open(self.app.current_pdf_path) as doc:
                        total_pages = len(doc)
            except:
                total_pages = 1

            def update_prog(p):
                if total_pages > 0:
                    val = (p / total_pages) * 100
                    self.app.after(0, lambda v=val, p=p, t=total_pages: 
                        self.app.status_controller.update_global_status_detail(v, p, t, start_time, self.app.current_pdf_path))
            
            def log_cb(msg):
                self.app.log_bridge(msg)
            
            # Switch to determinate immediately since we have total_pages
            self.app.after(0, lambda: self.app.status_controller.show_global_status(app_state.t("lbl_status_processing"), determinate=True))
            self.app.after(0, lambda: self.app.global_progress.config(mode="determinate", maximum=100, value=0))
            
            sidecar = run_ocr(
                self.app.current_pdf_path, 
                temp_out, 
                self.app.current_pdf_password, 
                self.app.var_force.get(),
                options=opts,
                progress_callback=update_prog,
                log_callback=log_cb
            )
            
            if self.stop_flag:
                raise Exception("Process Cancelled")
            self.app.after(0, lambda: self._on_process_success(temp_out, sidecar))
            
        except subprocess.CalledProcessError as e:
            if self.stop_flag:
                self.app.after(0, lambda: self._on_process_cancelled())
                return

            err_msg = str(e.stderr) if e.stderr else str(e)
            if len(err_msg) > 800:
                err_msg = "...(logs truncated)...\n" + err_msg[-800:]
                
            self.app.after(0, lambda: self._on_process_fail(err_msg))
            
        except Exception as e:
            err_msg = str(e)
            if "Process Cancelled" in err_msg or self.stop_flag:
                self.app.after(0, lambda: self._on_process_cancelled())
            else:
                self.app.after(0, lambda: self._on_process_fail(err_msg))

    def _on_process_cancelled(self):
        """Handle process cancellation."""
        self.app.status_controller.hide_global_status()
        self.app.btn_process.config(state="normal")
        self.app.lbl_status.config(text="Cancelled")
        fname = os.path.basename(self.app.current_pdf_path) if self.app.current_pdf_path else "Unknown"
        history.add_entry(fname, "Cancelled", source_path=self.app.current_pdf_path)
    
    def _on_process_fail(self, msg):
        """Handle process failure."""
        self.app.status_controller.hide_global_status()
        self.app.btn_process.config(state="normal")
        self.app.lbl_status.config(text="Failed.")
        fname = os.path.basename(self.app.current_pdf_path) if self.app.current_pdf_path else "Unknown"
        history.add_entry(fname, "Failed", source_path=self.app.current_pdf_path)
        messagebox.showerror("Error", msg)

    def _on_process_success(self, temp_out, sidecar):
        """Handle successful processing."""
        self.app.status_controller.hide_global_status()
        self.app.btn_process.config(state="normal")
        self.app.lbl_status.config(text=app_state.t("lbl_status_done"))
        fname = os.path.basename(self.app.current_pdf_path)
        size_mb = os.path.getsize(temp_out) / (1024 * 1024)
        history.add_entry(fname, "Completed", f"{size_mb:.1f} MB", source_path=self.app.current_pdf_path, output_path=temp_out)
        self.app.show_success_ui(temp_out, sidecar)

    # ==================== BATCH PROCESSING ====================
    
    def start_batch_processing(self):
        """Start batch processing for multiple files."""
        if not hasattr(self.app, 'batch_files') or not self.app.batch_files:
            messagebox.showwarning("Empty", "Please add files to process.")
            return
            
        from ...core import platform_utils
        out_dir = None
        if platform_utils.IS_LINUX:
            out_dir = platform_utils.linux_directory_dialog(
                title="Select Output Folder",
                initialdir=app_state.get_initial_dir()
            )
        else:
            out_dir = filedialog.askdirectory(title="Select Output Folder")

        if not out_dir:
            return
            
        if platform_utils.IS_LINUX:
            app_state.save_config({"last_open_dir": out_dir})
        
        self.app.save_settings_inline()

        self.app.btn_start_batch.config(state="disabled")
        self.stop_flag = False
        
        self.app.status_controller.show_global_status("Batch Processing Started...", determinate=True)
        self.app.status_controller.update_global_progress(0, len(self.app.batch_files) * 100)
        
        threading.Thread(target=self._run_batch_logic, args=(out_dir,), daemon=True).start()

    def add_batch_files(self):
        """Add files to the batch queue."""
        from ...core import platform_utils
        files = None
        if platform_utils.IS_LINUX:
            files = platform_utils.linux_file_dialog(
                title="Select PDF Files",
                initialdir=app_state.get_initial_dir(),
                multiple=True,
                filetypes=[("PDF files", "*.pdf")]
            )
        else:
            files = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])

        if not files:
            return
            
        if platform_utils.IS_LINUX:
            app_state.save_config({"last_open_dir": os.path.dirname(files[0])})
        if not hasattr(self.app, 'batch_files'):
            self.app.batch_files = []
        for f in files:
            if any(bf["path"] == f for bf in self.app.batch_files):
                continue
            item_id = self.app.batch_tree.insert("", "end", values=(os.path.basename(f), "Pending"))
            self.app.batch_files.append({"path": f, "id": item_id, "status": "Pending"})

    def clear_batch_files(self):
        """Clear all files from the batch queue."""
        self.app.batch_tree.delete(*self.app.batch_tree.get_children())
        self.app.batch_files = []

    def _run_batch_logic(self, out_dir):
        """Internal: Run batch processing logic."""
        print("Starting batch logic...")
        selected_langs = []
        if hasattr(self.app, 'batch_lang_vars'):
            for lang, var in self.app.batch_lang_vars.items():
                if var.get():
                    selected_langs.append(lang)
        
        print(f"Batch languages: {selected_langs}")

        if not selected_langs:
            print("No languages selected!")
            self.app.after(0, lambda: messagebox.showerror("Error", "No OCR languages selected for batch!"))
            self.app.after(0, lambda: self._on_batch_complete(0, len(self.app.batch_files)))
            return

        # Save selection
        try:
            app_state.set_option("last_used_ocr_languages", selected_langs)
            app_state.save_config({})
        except Exception as e:
            print(f"Config save error: {e}")

        ocr_lang = "+".join(selected_langs)
        print(f"OCR Lang string: {ocr_lang}")

        # Safe DPI parsing
        try:
            current_dpi = int(self.app.var_dpi.get())
        except:
            current_dpi = 300

        opts = {
            "language": ocr_lang,
            "deskew": self.app.var_deskew.get(),
            "clean": self.app.var_clean.get(),
            "rotate": self.app.var_rotate.get(),
            "optimize": self.app.var_optimize.get(),
            "use_gpu": self.app.var_gpu.get(),
            "gpu_device": self.app.var_gpu_device.get(),
            "max_cpu_threads": self.app.var_cpu_threads.get(),
            "rasterize": self.app.var_rasterize.get(),
            "dpi": current_dpi
        }
        
        success_count = 0
        total_docs = len(self.app.batch_files)
        
        for i, item in enumerate(self.app.batch_files):
            if self.stop_flag:
                break
            fpath = item["path"]
            item_id = item["id"]
            fname = os.path.basename(fpath)
            
            self.app.after(0, lambda id=item_id: self.app.batch_tree.set(id, "Status", "Processing..."))
            self.app.status_controller.reset_batch_page_counter()
            
            try:
                out_name = f"biplob_ocr_{fname}"
                out_path = os.path.join(out_dir, out_name)
                
                doc_total_pages = 1
                try:
                    with fitz.open(fpath) as d:
                        doc_total_pages = len(d)
                except:
                    pass
                
                file_start_time = time.time()

                def batch_prog_cb(p, i=i, fname=fname, doc_total_pages=doc_total_pages, 
                                  file_start_time=file_start_time, total_docs=total_docs, fpath=fpath):
                    if doc_total_pages > 0:
                        doc_pct = (p / doc_total_pages) * 100
                        global_val = (i * 100) + doc_pct
                        
                        elapsed = time.time() - file_start_time
                        avg_p = elapsed / p if p > 0 else 0
                        rem_p = doc_total_pages - p
                        etr = int(rem_p * avg_p)
                        etr_str = f"{etr//60}m {etr%60}s"
                        
                        self.app.after(0, lambda v=global_val, p=p, t=doc_total_pages, n=fname, idx=i+1, e=etr_str: 
                            self.app.status_controller.update_batch_status_detail(v, idx, total_docs, n, p, t, e, fpath))

                def log_cb(msg):
                    self.app.log_bridge(msg)

                try: 
                    with pikepdf.open(fpath):
                        pass
                except: 
                    raise Exception("Password Required")

                run_ocr(fpath, out_path, None, force=self.app.var_force.get(), options=opts, 
                       progress_callback=batch_prog_cb, log_callback=log_cb)
                
                if self.stop_flag:
                    raise Exception("Process Cancelled")
                     
                from ...core import platform_utils
                self.app.after(0, lambda id=item_id: self.app.batch_tree.set(id, "Status", platform_utils.sanitize_for_linux("✅ Done")))

                history.add_entry(fname, "Batch Success", "N/A", source_path=fpath, output_path=out_path)
                success_count += 1
                
            except Exception as e:
                from ...core import platform_utils
                status = platform_utils.sanitize_for_linux("❌ Failed")
                err_msg = str(e)
                if "Process Cancelled" in err_msg or self.stop_flag:
                    status = platform_utils.sanitize_for_linux("⛔ Cancelled")
                    self.app.after(0, lambda id=item_id, s=status: self.app.batch_tree.set(id, "Status", s))
                    history.add_entry(fname, "Batch Cancelled", source_path=fpath)
                    break
                self.app.after(0, lambda id=item_id, s=status: self.app.batch_tree.set(id, "Status", s))
                history.add_entry(fname, "Batch Failed", source_path=fpath)
            
            self.app.after(0, lambda v=(i+1)*100: self.app.global_progress.configure(value=v))
        
        self.app.after(0, lambda: self._on_batch_complete(success_count, total_docs))

    def _on_batch_complete(self, success, total):
        """Handle batch processing completion."""
        self.app.status_controller.hide_global_status()
        self.app.btn_start_batch.config(state="normal")
        if self.stop_flag:
            messagebox.showinfo("Batch Stopped", f"Processing Stopped.\nSuccessful: {success}")
        else:
            messagebox.showinfo("Batch Complete", f"Processed {total} files.\nSuccessful: {success}")
