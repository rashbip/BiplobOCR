"""
Status Controller - Manages the global status bar, progress updates, and ETR calculations.
Extracted from app.py for better maintainability.
"""
import time


class StatusController:
    """Handles status bar operations and progress tracking."""
    
    def __init__(self, app):
        self.app = app
        self.max_page_seen = 0
        self.batch_max_seen_page = 0
    
    def show_global_status(self, msg, determinate=False):
        """Show the global status bar with a message."""
        self.app.processing_active = True
        try:
            self.app.status_bar.pack(side="bottom", fill="x")
            self.app.lbl_global_status.config(text=msg)
            if determinate:
                self.app.global_progress.config(mode="determinate", value=0)
            else:
                self.app.global_progress.config(mode="indeterminate")
                self.app.global_progress.start(10)
        except: 
            pass

    def hide_global_status(self):
        """Hide the global status bar."""
        self.app.processing_active = False
        try:
            self.app.global_progress.stop()
        except: 
            pass
        try:
            self.app.status_bar.pack_forget()
        except: 
            pass

    def update_global_progress(self, val, max_val):
        """Update the progress bar value."""
        try:
            self.app.global_progress.config(mode="determinate", maximum=max_val, value=val)
        except: 
            pass

    def reset_page_counter(self):
        """Reset the page counter for a new processing session."""
        self.max_page_seen = 0

    def update_global_status_detail(self, val, page, total, start_time, pdf_path=None):
        """Update status with detailed progress including ETR calculation."""
        try:
            if total <= 0: return

            # If page is mistakenly a percentage > page count, normalize it
            if page > total:
                # If page is 100 or another high number, it's likely a percentage
                if page >= 20: # Heuristic: if >20 but total is e.g. 5, it's a percentage
                    val = page
                    page = total # Cap it
                else:
                    page = total

            real_val = (page / total) * 100
            self.app.global_progress["value"] = real_val
            
            # ETR Calculation
            elapsed = time.time() - start_time
            etr_str = "Calculating..."
            if page > 0:
                avg_sec_per_page = elapsed / page
                remaining_pages = max(0, total - page)
                etr_seconds = int(remaining_pages * avg_sec_per_page)
                
                # Format ETR
                if etr_seconds > 3600:
                    etr_str = f"{etr_seconds//3600}h {(etr_seconds%3600)//60}m"
                else:
                    etr_str = f"{etr_seconds//60}m {etr_seconds%60}s"
            
            txt = f"Processing Page {page} of {total} ({int(real_val)}%) - ETR: {etr_str}"
            
            # Update Status
            self.app.lbl_global_status.config(text=txt)

            # Update Log View Image ONLY on page change
            if page > self.max_page_seen:
                self.max_page_seen = page
                if hasattr(self.app, 'log_window') and self.app.log_window.winfo_exists() and pdf_path:
                    self.app.after(0, lambda: self.app.log_window.update_image(pdf_path, page - 1))
            
        except Exception as e: 
            pass

    def update_batch_status_detail(self, val, idx, total_docs, fname, page, total_pages, etr_str, pdf_path=None):
        """Update batch processing status with detailed progress."""
        # Monotonic progress check
        if page > self.batch_max_seen_page:
            self.batch_max_seen_page = page
            # Update Log View Image ONLY on page change
            if hasattr(self.app, 'log_window') and self.app.log_window.winfo_exists() and pdf_path:
                self.app.after(0, lambda: self.app.log_window.update_image(pdf_path, page - 1))
        else:
            page = self.batch_max_seen_page

        self.app.global_progress.configure(maximum=total_docs * 100, value=val)
        self.app.lbl_global_status.config(
            text=f"[{idx}/{total_docs}] {fname}: Page {page}/{total_pages} ({int((page/total_pages)*100)}%) - ETR: {etr_str}"
        )

    def reset_batch_page_counter(self):
        """Reset the batch page counter for a new file."""
        self.batch_max_seen_page = 0
