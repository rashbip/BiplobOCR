import tkinter as tk
from tkinter import ttk, messagebox
from tkinterdnd2 import DND_FILES
import os
from ...core.history_manager import history
from ...core.theme import SURFACE_COLOR, THEME_COLOR, MAIN_FONT, HEADER_FONT
from ...core.config_manager import state as app_state
from ...core import platform_utils
from ...core.emoji_label import EmojiLabel, render_emoji_image



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
        EmojiLabel(self, text=app_state.t("home_welcome"), font=(HEADER_FONT, 30, "bold"), foreground=THEME_COLOR).pack(anchor="w")
        EmojiLabel(self, text=app_state.t("home_desc"), font=(MAIN_FONT, 14), foreground="gray").pack(anchor="w", pady=(5, 30))


        
        cards_frame = ttk.Frame(self)
        cards_frame.pack(fill="x", pady=20)
        
        # Card 1: New Task
        card1 = ttk.Frame(cards_frame, style="Card.TFrame", padding=1)
        card1.pack(side="left", fill="both", expand=True, padx=(0, 10))
        c1_inner = ttk.Frame(card1, padding=30, style="Card.TFrame")
        c1_inner.pack(fill="both", expand=True)
        EmojiLabel(c1_inner, text="📂", font=(MAIN_FONT, 48), background=SURFACE_COLOR).pack(pady=(0,10))
        EmojiLabel(c1_inner, text=app_state.t("card_new_task"), font=(MAIN_FONT, 22, "bold"), background=SURFACE_COLOR).pack()
        EmojiLabel(c1_inner, text=app_state.t("card_new_desc"), font=(MAIN_FONT, 16), foreground="gray", background=SURFACE_COLOR).pack(pady=5)




        btn_select = ttk.Button(c1_inner, text="", style="Accent.TButton", command=self.controller.open_pdf_from_home)
        img_sel = render_emoji_image(app_state.t("btn_select_computer"), (MAIN_FONT, 16), "white", btn_select)
        if img_sel:
            btn_select.config(image=img_sel)
            btn_select._img = img_sel
        else:
            btn_select.config(text=app_state.t("btn_select_computer"))
        btn_select.pack(pady=20, ipadx=10, ipady=5)

        
        # Card 2: Batch Process
        card2 = ttk.Frame(cards_frame, style="Card.TFrame", padding=1)
        card2.pack(side="left", fill="both", expand=True, padx=(10, 0))
        c2_inner = ttk.Frame(card2, padding=30, style="Card.TFrame")
        c2_inner.pack(fill="both", expand=True)
        EmojiLabel(c2_inner, text="📦", font=(MAIN_FONT, 48), background=SURFACE_COLOR).pack(pady=(0,10))
        EmojiLabel(c2_inner, text=app_state.t("batch_title"), font=(MAIN_FONT, 22, "bold"), background=SURFACE_COLOR).pack()
        EmojiLabel(c2_inner, text="Process multiple PDFs at once", font=(MAIN_FONT, 16), foreground="gray", background=SURFACE_COLOR).pack(pady=5)




        
        btn_batch_tool = ttk.Button(c2_inner, text="", style="TButton", command=lambda: self.controller.switch_tab("batch"))
        img_batch = render_emoji_image("Open Batch Tool", (MAIN_FONT, 16), "white", btn_batch_tool)
        if img_batch:
            btn_batch_tool.config(image=img_batch)
            btn_batch_tool._img = img_batch
        else:
            btn_batch_tool.config(text="Open Batch Tool")
        btn_batch_tool.pack(pady=20, ipadx=10, ipady=5)

        # The following line was incorrectly indented in the instruction. Assuming it was meant to be removed or part of the lambda.
        # self.controller.add_batch_files() 
        # The instruction also included the old button, which is now replaced by the above.
        # ttk.Button(c2_inner, text=app_state.t("btn_open_batch"), style="Accent.TButton", command=open_batch_diag).pack(pady=20, ipadx=10, ipady=5)

        # Recent Documents (Cards)
        EmojiLabel(self, text=app_state.t("home_recent"), font=(MAIN_FONT, 20, "bold")).pack(anchor="w", pady=(40, 10))


        
        self.recent_container = ttk.Frame(self)
        self.recent_container.pack(fill="both", expand=True)
        
        self.refresh_recent_docs()

    def refresh_recent_docs(self):
        for widget in self.recent_container.winfo_children(): widget.destroy()
        
        data = history.get_all()
        if not data:
            EmojiLabel(self.recent_container, text="No recent activity", foreground="gray", font=(MAIN_FONT, 14)).pack(anchor="w", pady=10)

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
        
        EmojiLabel(info_frame, text=fname, font=(MAIN_FONT, 12, "bold"), background=SURFACE_COLOR).pack(anchor="w")
        
        meta_txt = f"{date_str} • {status}"
        lbl_meta = EmojiLabel(info_frame, text=meta_txt, font=(MAIN_FONT, 10), background=SURFACE_COLOR)
        lbl_meta.config(foreground="gray")
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

        btn_src = ttk.Button(actions, command=open_src)
        img_src = render_emoji_image("📂 Src", (MAIN_FONT, 12), "white", btn_src)
        if img_src:
            btn_src.config(image=img_src, text="")
            btn_src._img = img_src
        else:
            btn_src.config(text="📂 Src")
        btn_src.pack(side="left", padx=2)
        if not source: btn_src.config(state="disabled")

        
        # 2. Output Open
        def open_out():
            if output and os.path.exists(output):
                self.controller.open_dropped_pdf(output)
            else:
                messagebox.showerror("Error", "Output file not found.")

        btn_out = ttk.Button(actions, command=open_out)
        img_out = render_emoji_image("👁 View", (MAIN_FONT, 12), "white", btn_out)
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
                # We need to find the correct index in standard history
                # Since we are iterating 0..5 of get_all(), the 'index' passed in is correct
                history.delete_entry(index)
                self.refresh_recent_docs()

        btn_del = ttk.Button(actions, style="Danger.TButton", command=delete_me)
        img_del = render_emoji_image("🗑", (MAIN_FONT, 12), "white", btn_del)
        if img_del:
            btn_del.config(image=img_del, text="")
            btn_del._img = img_del
        else:
            btn_del.config(text="🗑")
        btn_del.pack(side="left", padx=2)
