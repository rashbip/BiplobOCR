import tkinter as tk
from tkinter import ttk, messagebox
from ...core.history_manager import history
from ...core.theme import SURFACE_COLOR

class HistoryView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=40)
        self.controller = controller
        self.build_ui()

    def build_ui(self):
        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 20))
        
        ttk.Label(header, text="History Logs", style="Header.TLabel").pack(side="left")
        ttk.Button(header, text="🗑 Clear All", command=self.confirm_clear_all, style="Danger.TButton").pack(side="right")

        cols = ("Filename", "Date", "Size", "Status")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        self.tree.pack(fill="both", expand=True)
        
        self.tree.heading("Filename", text="Filename")
        self.tree.heading("Date", text="Date")
        self.tree.heading("Size", text="Size")
        self.tree.heading("Status", text="Status")
        
        self.tree.column("Filename", width=300)
        self.tree.column("Date", width=150)
        self.tree.column("Size", width=80)
        self.tree.column("Status", width=100)

        # Scrollbar
        sb = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")

        # Context Menu
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Delete", command=self.delete_selected)
        self.tree.bind("<Button-3>", self.show_context_menu)

        self.refresh()

    def refresh(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        data = history.get_all()
        for i, item in enumerate(data): 
             # Store index in iid to map back to list
            self.tree.insert("", "end", iid=str(i), values=(item["filename"], item["date"], item["size"], item["status"]))

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.menu.post(event.x_root, event.y_root)

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected: return
        
        # We need to handle multiple deletions carefully because indices shift
        # But we used iid=str(index). 
        # Actually, if we delete index 0, index 1 becomes 0. So static IID mapping is dangerous if we don't refresh immediately.
        # Safest way: Get integer indices, sort descending, delete from manager.
        
        indices = [int(iid) for iid in selected]
        indices.sort(reverse=True)
        
        for idx in indices:
            history.delete_entry(idx)
            
        self.refresh()
        self.controller.view_home.refresh_recent_docs() # Update home too

    def confirm_clear_all(self):
        if messagebox.askyesno("Confirm", "Clear entire history log?"):
            history.clear_all()
            self.refresh()
            self.controller.view_home.refresh_recent_docs()
