import tkinter as tk
from tkinter import ttk, messagebox
import os
from ...core.history_manager import history
from ...core.theme import SURFACE_COLOR, BG_COLOR, THEME_COLOR, FG_COLOR, MAIN_FONT, HEADER_FONT
from ...core.config_manager import state as app_state
from ...core import platform_utils
from ...core.emoji_label import EmojiLabel, render_emoji_image



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

        # Scrollable Area
        self.canvas = tk.Canvas(self, bg=SURFACE_COLOR, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas, style="Card.TFrame")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Store window id to update width later
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, pady=10)
        self.scrollbar.pack(side="right", fill="y", pady=10)
        
        # Responsive Width Binding
        self.canvas.bind('<Configure>', self._on_canvas_configure)

        # Mousewheel
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.refresh()
        
    def _on_canvas_configure(self, event):
        # Update the width of the frame to fill the canvas
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

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
            
        # Header Row (Inside scrollable frame or separate? separate is better for sticky header but let's put simple labels)
        # Actually separate header is better, but since rows are responsive, columns might misalign if header is separate and static.
        # For true responsiveness with aligned columns, grid is best. But simple "Name... ....... Date Status Action" works too.
        # Let's keep it simple: Just rows.
        
        for i, item in enumerate(data):
            self.create_history_row(i, item)

    def create_history_row(self, index, item):
        row = ttk.Frame(self.scrollable_frame, style="Card.TFrame", padding=(10, 5))
        row.pack(fill="x", pady=2, padx=2) 
        
        # Data
        fname = item.get("filename", "Unknown")
        date_str = item.get("date", "")
        status = item.get("status", "")
        source = item.get("source_path")
        output = item.get("output_path")
        
        # Layout: [Name (Expand)] [Date (Fixed)] [Status (Fixed)] [Actions (Fixed)]
        
        # Actions Panel (Right)
        actions = ttk.Frame(row, style="Card.TFrame")
        actions.pack(side="right", padx=10)

        # 1. Source System
        def open_src():
            if source and os.path.exists(source):
                self.controller.open_dropped_pdf(source)
            else:
                messagebox.showerror("Error", "Source file not found (Moved/Deleted).")

        btn_src = ttk.Button(actions, command=open_src)
        img_src = render_emoji_image("📄 Src", (MAIN_FONT, 10), "white", btn_src)


        if img_src:
            btn_src.config(image=img_src, text="")
            btn_src._img = img_src
        else:
            btn_src.config(text="📄 Src")
        btn_src.pack(side="left", padx=2)

        if not source: btn_src.config(state="disabled")
        
        # 2. Output Open
        def open_out():
            if output and os.path.exists(output):
                self.controller.open_dropped_pdf(output)
            else:
                messagebox.showerror("Error", "Output file not found (Moved/Deleted).")

        btn_out = ttk.Button(actions, command=open_out)
        img_out = render_emoji_image("👁 View", (MAIN_FONT, 10), "white", btn_out)


        if img_out:
            btn_out.config(image=img_out, text="")
            btn_out._img = img_out
        else:
            btn_out.config(text="👁 View")
        btn_out.pack(side="left", padx=2)

        
        if not output:
            btn_out.config(state="disabled")

        # 3. Delete
        def delete_me():
            if messagebox.askyesno("Delete", f"Delete history for {fname}?"):
                history.delete_entry(index)
                self.refresh()
                self.controller.view_home.refresh_recent_docs()

        btn_del = ttk.Button(actions, style="Danger.TButton", command=delete_me)
        img_del = render_emoji_image("🗑 Del", (MAIN_FONT, 10), "white", btn_del)


        if img_del:
            btn_del.config(image=img_del, text="")
            btn_del._img = img_del
        else:
            btn_del.config(text="🗑 Del")
        btn_del.pack(side="left", padx=2)

        
        # Status (Before Actions)
        lbl_status = EmojiLabel(row, text=status, width=15, font=(MAIN_FONT, 11, "bold"), background=SURFACE_COLOR)

        if "Success" in status or "Completed" in status: lbl_status.config(foreground="#4CAF50")
        elif "Fail" in status: lbl_status.config(foreground="#F44336")
        else: lbl_status.config(foreground="orange")
        lbl_status.pack(side="right", padx=10)
        
        # Date (Before Status)
        lbl_date = ttk.Label(row, text=date_str, width=20, font=(MAIN_FONT, 9), foreground="gray", background=SURFACE_COLOR)
        lbl_date.pack(side="right", padx=10)
        
        # Name (Left, Expand)
        # Dynamic truncation could be hard with pure Label, but let's try just letting it cut off or wrap
        # But user wants responsive. 
        lbl_name = ttk.Label(row, text=fname, font=(MAIN_FONT, 10), background=SURFACE_COLOR)
        lbl_name.pack(side="left", fill="x", expand=True, padx=10)

    def confirm_clear_all(self):
        if messagebox.askyesno("Confirm", "Clear entire history log?"):
            history.clear_all()
            self.refresh()
            self.controller.view_home.refresh_recent_docs()

