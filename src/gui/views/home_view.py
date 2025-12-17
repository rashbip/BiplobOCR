import tkinter as tk
from tkinter import ttk
from ...core.history_manager import history
from ...core.theme import SURFACE_COLOR, THEME_COLOR

class HomeView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=40)
        self.controller = controller
        self.build_ui()

    def build_ui(self):
        ttk.Label(self, text="Welcome to BiplobOCR", style="Header.TLabel").pack(anchor="w")
        ttk.Label(self, text="Ready to digitize your documents? Start a new scan or pick up where you left off.", font=("Segoe UI", 12), foreground="gray").pack(anchor="w", pady=(5, 30))
        
        cards_frame = ttk.Frame(self)
        cards_frame.pack(fill="x", pady=20)
        
        # Start Card
        card1 = ttk.Frame(cards_frame, style="Card.TFrame", padding=2)
        card1.pack(side="left", fill="both", expand=True, padx=(0, 10))
        c1_inner = ttk.Frame(card1, padding=30, style="Card.TFrame")
        c1_inner.pack(fill="both", expand=True)
        ttk.Label(c1_inner, text="📂", font=("Segoe UI", 32), background=SURFACE_COLOR).pack(pady=(0,10))
        ttk.Label(c1_inner, text="Start a new OCR task", font=("Segoe UI", 16, "bold"), background=SURFACE_COLOR).pack()
        ttk.Label(c1_inner, text="Securely process PDF, JPG, PNG", foreground="gray", background=SURFACE_COLOR).pack(pady=5)
        ttk.Button(c1_inner, text="Select from Computer", style="Accent.TButton", command=self.controller.open_pdf_from_home).pack(pady=20, ipadx=10, ipady=5)
        
        # Batch Card
        card2 = ttk.Frame(cards_frame, style="Card.TFrame", padding=2)
        card2.pack(side="left", fill="both", expand=True, padx=(10, 0))
        c2_inner = ttk.Frame(card2, padding=30, style="Card.TFrame")
        c2_inner.pack(fill="both", expand=True)
        ttk.Label(c2_inner, text="📦", font=("Segoe UI", 32), background=SURFACE_COLOR).pack(pady=(0,10))
        ttk.Label(c2_inner, text="Batch Process", font=("Segoe UI", 16, "bold"), background=SURFACE_COLOR).pack()
        ttk.Button(c2_inner, text="Open Batch Tool", command=lambda: self.controller.switch_tab("batch")).pack(pady=20)

        # Recent Documents
        ttk.Label(self, text="Recent Activity", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(40, 10))
        
        cols = ("Filename", "Date", "Status")
        self.tree_recent = ttk.Treeview(self, columns=cols, show="headings", height=6)
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
