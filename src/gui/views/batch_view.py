import tkinter as tk
from tkinter import ttk
from ...core.theme import SURFACE_COLOR, THEME_COLOR

class BatchView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=40)
        self.controller = controller
        self.build_ui()

    def build_ui(self):
        ttk.Label(self, text="Batch Processing", style="Header.TLabel").pack(anchor="w", pady=(20, 10))
        ttk.Label(self, text="Process multiple documents automatically.", foreground="gray").pack(anchor="w", pady=(0, 20))
        
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=5)
        ttk.Button(toolbar, text="➕ Add Files", command=self.controller.add_batch_files, style="Accent.TButton", width=15).pack(side="left", padx=(0, 5))
        ttk.Button(toolbar, text="🗑 Clear List", command=self.controller.clear_batch_files).pack(side="left")

        cols = ("Filename", "Status")
        self.controller.batch_tree = ttk.Treeview(self, columns=cols, show="headings", height=10)
        self.controller.batch_tree.pack(fill="both", expand=True, pady=10)
        self.controller.batch_tree.heading("Filename", text="Filename")
        self.controller.batch_tree.heading("Status", text="Status")
        self.controller.batch_tree.column("Filename", width=400)
        self.controller.batch_tree.column("Status", width=150)
        
        controls = ttk.Frame(self, padding=10, style="Card.TFrame")
        controls.pack(fill="x", pady=10)
        
        opt_box = ttk.Frame(controls, style="Card.TFrame")
        opt_box.pack(side="left", fill="both", expand=True)
        ttk.Label(opt_box, text="Batch Options", font=("Segoe UI", 10, "bold"), background=SURFACE_COLOR).pack(anchor="w")
        ttk.Checkbutton(opt_box, text="Deskew", variable=self.controller.var_deskew).pack(side="left", padx=5)
        ttk.Checkbutton(opt_box, text="Clean", variable=self.controller.var_clean).pack(side="left", padx=5)
        
        self.controller.btn_start_batch = ttk.Button(controls, text="▶ Start Batch", command=self.controller.start_batch_processing, style="Accent.TButton", width=20)
        self.controller.btn_start_batch.pack(side="right")
