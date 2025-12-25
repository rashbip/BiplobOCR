import tkinter as tk
from tkinter import ttk, messagebox
from tkinterdnd2 import DND_FILES
import os
from ...core.history_manager import history
from ...core.theme import SURFACE_COLOR, THEME_COLOR, MAIN_FONT, HEADER_FONT
from ...core.config_manager import state as app_state
from ...core import platform_utils

class HomeView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=40)
        self.controller = controller
        
        self.build_ui()
        
        # Drag & Drop Registration
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.on_drop)
        
    def on_drop(self, event):
        if event.data:
            self.controller.open_dropped_pdf(event.data)

    def build_ui(self):
        ttk.Label(self, text=app_state.t("home_welcome"), style="Header.TLabel").pack(anchor="w")
        ttk.Label(self, text=app_state.t("home_desc"), font=(MAIN_FONT, 12), foreground="gray").pack(anchor="w", pady=(5, 30))
        
        cards_frame = ttk.Frame(self)
        cards_frame.pack(fill="x", pady=20)
        
        # Start Card
        card1 = ttk.Frame(cards_frame, style="Card.TFrame", padding=2)
        card1.pack(side="left", fill="both", expand=True, padx=(0, 10))
        c1_inner = ttk.Frame(card1, padding=30, style="Card.TFrame")
        c1_inner.pack(fill="both", expand=True)
        ttk.Label(c1_inner, text=platform_utils.sanitize_for_linux("📂"), font=(MAIN_FONT, 32), background=SURFACE_COLOR).pack(pady=(0,10))
        ttk.Label(c1_inner, text=app_state.t("card_new_task"), font=(MAIN_FONT, 16, "bold"), background=SURFACE_COLOR).pack()
        ttk.Label(c1_inner, text=app_state.t("card_new_desc"), font=(MAIN_FONT, 10), foreground="gray", background=SURFACE_COLOR).pack(pady=5)
        ttk.Button(c1_inner, text=app_state.t("btn_select_computer"), style="Accent.TButton", command=self.controller.open_pdf_from_home).pack(pady=20, ipadx=10, ipady=5)
        
        # Batch Card
        card2 = ttk.Frame(cards_frame, style="Card.TFrame", padding=2)
        card2.pack(side="left", fill="both", expand=True, padx=(10, 0))
        c2_inner = ttk.Frame(card2, padding=30, style="Card.TFrame")
        c2_inner.pack(fill="both", expand=True)
        ttk.Label(c2_inner, text=platform_utils.sanitize_for_linux("📦"), font=(MAIN_FONT, 32), background=SURFACE_COLOR).pack(pady=(0,10))
        ttk.Label(c2_inner, text=app_state.t("batch_title"), font=(MAIN_FONT, 16, "bold"), background=SURFACE_COLOR).pack()
        ttk.Label(c2_inner, text="Process multiple PDFs at once", font=(MAIN_FONT, 10), foreground="gray", background=SURFACE_COLOR).pack(pady=5)
        
        def open_batch_diag():
            self.controller.switch_tab("batch")
            self.controller.add_batch_files()
            
        ttk.Button(c2_inner, text=app_state.t("btn_open_batch"), style="Accent.TButton", command=open_batch_diag).pack(pady=20, ipadx=10, ipady=5)

        # Recent Documents (Cards)
        ttk.Label(self, text=app_state.t("home_recent"), font=(MAIN_FONT, 16, "bold")).pack(anchor="w", pady=(40, 10))
        
        self.recent_container = ttk.Frame(self)
        self.recent_container.pack(fill="both", expand=True)
        
        self.refresh_recent_docs()

    def refresh_recent_docs(self):
        for widget in self.recent_container.winfo_children(): widget.destroy()
        
        data = history.get_all()
        if not data:
            ttk.Label(self.recent_container, text="No recent activity", foreground="gray").pack(anchor="w", pady=10)
            return

        for i, item in enumerate(data):
            if i >= 5: break
            self.create_mini_history_row(i, item)
            
    def create_mini_history_row(self, index, item):
        row = ttk.Frame(self.recent_container, style="Card.TFrame", padding=10)
        row.pack(fill="x", pady=2)
        
        fname = item.get("filename", "Unknown")
        date_str = item.get("date", "")
        status = item.get("status", "")
        source = item.get("source_path")
        output = item.get("output_path")
        
        # Info
        info_frame = ttk.Frame(row, style="Card.TFrame")
        info_frame.pack(side="left", fill="x", expand=True)
        
        ttk.Label(info_frame, text=fname, font=(MAIN_FONT, 10, "bold"), background=SURFACE_COLOR).pack(anchor="w")
        
        meta_txt = f"{date_str} • {status}"
        lbl_meta = ttk.Label(info_frame, text=meta_txt, font=(MAIN_FONT, 9), background=SURFACE_COLOR, foreground="gray")
        lbl_meta.pack(anchor="w")
        
        # Actions
        actions = ttk.Frame(row, style="Card.TFrame")
        actions.pack(side="right")
        
        # 1. Source System
        def open_src():
            if source and os.path.exists(source):
                self.controller.open_dropped_pdf(source)
            else:
                messagebox.showerror("Error", "Source file not found.")

        btn_src = tk.Button(actions, text=platform_utils.sanitize_for_linux("📄 Src"), font=(MAIN_FONT, 8), bg="#3e3e3e", fg="white", bd=0, padx=8, pady=4, cursor="hand2", command=open_src)
        btn_src.pack(side="left", padx=2)
        if not source: btn_src.config(state="disabled", bg="#2a2a2a", fg="gray")
        
        # 2. Output Open
        def open_out():
            if output and os.path.exists(output):
                self.controller.open_dropped_pdf(output)
            else:
                messagebox.showerror("Error", "Output file not found.")

        btn_out = tk.Button(actions, text=platform_utils.sanitize_for_linux("👁 View"), font=(MAIN_FONT, 8), bg=THEME_COLOR, fg="white", bd=0, padx=8, pady=4, cursor="hand2", command=open_out)
        btn_out.pack(side="left", padx=2)
        if not output: btn_out.config(state="disabled", bg="#2a2a2a", fg="gray", cursor="arrow")

        # 3. Delete
        def delete_me():
            if messagebox.askyesno("Delete", f"Delete history for {fname}?"):
                # We need to find the correct index in standard history
                # Since we are iterating 0..5 of get_all(), the 'index' passed in is correct
                history.delete_entry(index)
                self.refresh_recent_docs()

        btn_del = tk.Button(actions, text=platform_utils.sanitize_for_linux("🗑"), font=(MAIN_FONT, 8), bg="#2a2a2a", fg="#ff5555", bd=0, padx=8, pady=4, cursor="hand2", command=delete_me)
        btn_del.pack(side="left", padx=2)
