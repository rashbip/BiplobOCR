import tkinter as tk
from tkinter import ttk, messagebox
import os
from ...core.history_manager import history
from ...core.theme import SURFACE_COLOR, BG_COLOR, THEME_COLOR, FG_COLOR
from ...core.config_manager import state as app_state

class HistoryView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=40)
        self.controller = controller
        self.build_ui()

    def build_ui(self):
        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 20))
        
        ttk.Label(header, text=app_state.t("nav_history"), style="Header.TLabel").pack(side="left")
        ttk.Button(header, text=app_state.t("btn_clear_history"), command=self.confirm_clear_all, style="Danger.TButton").pack(side="right")

        # Column Headers (Visual Only)
        cols_frame = ttk.Frame(self, style="Card.TFrame", padding=5)
        cols_frame.pack(fill="x")
        ttk.Label(cols_frame, text=app_state.t("col_filename"), width=40, font=("Segoe UI", 9, "bold"), background=SURFACE_COLOR).pack(side="left", padx=10)
        ttk.Label(cols_frame, text=app_state.t("col_date"), width=20, font=("Segoe UI", 9, "bold"), background=SURFACE_COLOR).pack(side="left")
        ttk.Label(cols_frame, text="Actions", font=("Segoe UI", 9, "bold"), background=SURFACE_COLOR).pack(side="right", padx=20)
        
        # Scrollable Area
        self.canvas = tk.Canvas(self, bg=SURFACE_COLOR, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas, style="Card.TFrame")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=1200) # Fixed width or adjust dynamic
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, pady=10)
        self.scrollbar.pack(side="right", fill="y", pady=10)
        
        # Mousewheel
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.refresh()
        
    def _on_mousewheel(self, event):
        try:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except: pass

    def refresh(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        data = history.get_all()
        if not data:
            ttk.Label(self.scrollable_frame, text="No History Found", background=SURFACE_COLOR).pack(pady=20)
            return

        for i, item in enumerate(data):
            self.create_history_row(i, item)

    def create_history_row(self, index, item):
        row = ttk.Frame(self.scrollable_frame, style="Card.TFrame", padding=(10, 5))
        row.pack(fill="x", pady=2)
        
        # Data
        fname = item.get("filename", "Unknown")
        date_str = item.get("date", "")
        status = item.get("status", "")
        source = item.get("source_path")
        output = item.get("output_path")
        
        # Shorten filename if needed
        disp_name = (fname[:35] + '..') if len(fname) > 35 else fname
        
        lbl_name = ttk.Label(row, text=disp_name, width=40, font=("Segoe UI", 10), background=SURFACE_COLOR)
        lbl_name.pack(side="left", padx=10)
        
        lbl_date = ttk.Label(row, text=date_str, width=20, font=("Segoe UI", 9), foreground="gray", background=SURFACE_COLOR)
        lbl_date.pack(side="left")
        
        lbl_status = ttk.Label(row, text=status, width=15, font=("Segoe UI", 9, "bold"), background=SURFACE_COLOR)
        if "Success" in status or "Completed" in status: lbl_status.config(foreground="#4CAF50")
        elif "Fail" in status: lbl_status.config(foreground="#F44336")
        else: lbl_status.config(foreground="orange")
        lbl_status.pack(side="left")

        # Actions Panel
        actions = ttk.Frame(row, style="Card.TFrame")
        actions.pack(side="right", padx=10)

        # 1. Source System
        def open_src():
            if source and os.path.exists(source):
                self.controller.open_dropped_pdf(source)
            else:
                messagebox.showerror("Error", "Source file not found (Moved/Deleted).")

        btn_src = tk.Button(actions, text="📄 Src", font=("Segoe UI", 8), bg="#3e3e3e", fg="white", bd=0, padx=8, pady=4, cursor="hand2", command=open_src)
        btn_src.pack(side="left", padx=2)
        if not source: btn_src.config(state="disabled", bg="#2a2a2a", fg="gray")
        
        # 2. Output Open
        def open_out():
            if output and os.path.exists(output):
                self.controller.open_dropped_pdf(output)
            else:
                messagebox.showerror("Error", "Output file not found (Moved/Deleted).")

        btn_out = tk.Button(actions, text="👁 View", font=("Segoe UI", 8), bg=THEME_COLOR, fg="white", bd=0, padx=8, pady=4, cursor="hand2", command=open_out)
        btn_out.pack(side="left", padx=2)
        
        # Disable output button if not success or path missing
        if not output:
            btn_out.config(state="disabled", bg="#2a2a2a", fg="gray", cursor="arrow")

        # 3. Delete
        def delete_me():
            if messagebox.askyesno("Delete", f"Delete history for {fname}?"):
                history.delete_entry(index)
                self.refresh()
                self.controller.view_home.refresh_recent_docs()

        btn_del = tk.Button(actions, text="🗑", font=("Segoe UI", 8), bg="#2a2a2a", fg="#ff5555", bd=0, padx=8, pady=4, cursor="hand2", command=delete_me)
        btn_del.pack(side="left", padx=2)

    def confirm_clear_all(self):
        if messagebox.askyesno("Confirm", "Clear entire history log?"):
            history.clear_all()
            self.refresh()
            self.controller.view_home.refresh_recent_docs()

