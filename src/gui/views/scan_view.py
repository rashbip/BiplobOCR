"""
Scan View - The main single-file OCR processing view.
Extracted from app.py for better maintainability.
"""
import tkinter as tk
from tkinter import ttk

from ...core.theme import SURFACE_COLOR, THEME_COLOR, MAIN_FONT, HEADER_FONT
from ...core.config_manager import state as app_state
from ...core.ocr_engine import get_available_languages
from ...core import platform_utils
from ...core.emoji_label import EmojiLabel, render_emoji_image


from ..pdf_viewer import PDFViewer

class ScanView(ttk.Frame):
    """View for single PDF OCR processing."""
    
    def __init__(self, parent, controller):

        super().__init__(parent)
        self.controller = controller
        self.build_ui()
        
        # Drag & Drop Registration
        try:
            from tkinterdnd2 import DND_FILES
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self.on_drop)
        except: pass

    def on_drop(self, event):
        if event.data:
            self.controller.open_dropped_pdf(event.data)
    
    def _create_check(self, parent, text, var):
        """Helper to create a checkbutton with custom font support via EmojiLabel."""
        f = ttk.Frame(parent)
        f.pack(anchor="w", pady=1)
        c = ttk.Checkbutton(f, variable=var)
        c.pack(side="left")
        l = EmojiLabel(f, text=text, font=(MAIN_FONT, 12))
        l.pack(side="left", padx=5)
        # Clicking label toggles check
        l.bind("<Button-1>", lambda e: var.set(not var.get()))
        return f

    
    def build_ui(self):
        """Build the scan view UI."""
        self.scan_paned = ttk.PanedWindow(self, orient="horizontal")
        self.scan_paned.pack(fill="both", expand=True)
        
        # --- Sidebar ---
        self.scan_sidebar = ttk.Frame(self.scan_paned, width=300, padding=15)
        self.scan_paned.add(self.scan_sidebar, weight=0)
        
        EmojiLabel(self.scan_sidebar, text="Active Task", font=(HEADER_FONT, 14, "bold"), 
                  foreground=THEME_COLOR).pack(anchor="w", pady=(0, 20))

        btn_open = ttk.Button(self.scan_sidebar, command=self.controller.open_pdf, style="Accent.TButton")
        img_open = render_emoji_image(app_state.t("btn_open_computer", sanitize=False), (MAIN_FONT, 18), "white", btn_open)
        if img_open:
            btn_open.config(image=img_open, text="")
            btn_open._img = img_open
        else:
            btn_open.config(text=app_state.t("btn_open_computer", sanitize=False))


        btn_open.pack(fill="x", pady=2)

        
        # Options
        opt_group = ttk.Frame(self.scan_sidebar, padding=10, style="Card.TFrame")
        opt_group.pack(fill="x", pady=10)
        EmojiLabel(opt_group, text=app_state.t("grp_options"), font=(MAIN_FONT, 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        self._create_check(opt_group, app_state.t("opt_deskew"), self.controller.var_deskew)
        self._create_check(opt_group, app_state.t("opt_clean"), self.controller.var_clean)
        self._create_check(opt_group, app_state.t("opt_rotate"), self.controller.var_rotate)
        self._create_check(opt_group, app_state.t("opt_force"), self.controller.var_force)
        self._create_check(opt_group, app_state.t("opt_rasterize"), self.controller.var_rasterize)

        
        dpi_frame = ttk.Frame(opt_group)
        dpi_frame.pack(fill="x", pady=5)
        EmojiLabel(dpi_frame, text=app_state.t("lbl_dpi"), font=(MAIN_FONT, 14)).pack(side="left")

        ttk.Entry(dpi_frame, textvariable=self.controller.var_dpi, width=8).pack(side="right")

        EmojiLabel(opt_group, text=app_state.t("lbl_optimize"), font=(MAIN_FONT, 14)).pack(anchor="w", pady=(10, 2))
        ttk.Combobox(opt_group, textvariable=self.controller.var_optimize, 
                     values=["0", "1", "2", "3"], state="readonly").pack(fill="x")


        # Multi-Select Languages
        lang_group = ttk.Frame(self.scan_sidebar, padding=10, style="Card.TFrame")
        lang_group.pack(fill="x", pady=10)
        EmojiLabel(lang_group, text="Processing Languages", font=(MAIN_FONT, 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        # Container for dynamic language list
        self.lang_container = ttk.Frame(lang_group)

        self.lang_container.pack(fill="x", expand=True)
        
        # Build initial language list
        self._build_language_checkboxes()

        # Process Button
        self.controller.btn_process = ttk.Button(
            self.scan_sidebar, text="", 
            command=self.controller.processing_controller.start_processing_thread, 
            state="disabled", style="Accent.TButton"
        )
        img_proc = render_emoji_image(app_state.t("btn_process"), (MAIN_FONT, 18), "white", self.controller.btn_process)
        if img_proc:
            self.controller.btn_process.config(image=img_proc)
            self.controller.btn_process._img = img_proc
        else:
            self.controller.btn_process.config(text=app_state.t("btn_process"))

        self.controller.btn_process.pack(fill="x", pady=20)
        
        # Status Label
        self.controller.lbl_status = EmojiLabel(
            self.scan_sidebar, text="Ready", font=(MAIN_FONT, 16, "bold"), foreground=THEME_COLOR, wraplength=250
        )
        self.controller.lbl_status.pack(anchor="w", pady=5)
        
        # --- Viewer Container ---
        self.viewer_container = ttk.Frame(self.scan_paned)
        self.scan_paned.add(self.viewer_container, weight=1)
        
        self.controller.viewer = PDFViewer(self.viewer_container)
        self.controller.viewer.pack(fill="both", expand=True)
        
        self.controller.success_frame = ttk.Frame(self.viewer_container, style="Card.TFrame", padding=20)



    def _build_language_checkboxes(self):
        """Build or rebuild the language checkboxes."""
        # Clear existing
        for widget in self.lang_container.winfo_children():
            widget.destroy()
        
        # Load available and previously selected
        avail = get_available_languages()
        last_used = app_state.get("last_used_ocr_languages")
        if not last_used:
            last_used = [app_state.get("ocr_language", "eng")]
        
        # Scrollable container for langs with FIXED HEIGHT
        lc = tk.Canvas(self.lang_container, bg=SURFACE_COLOR, highlightthickness=0, height=120)
        ls = ttk.Scrollbar(self.lang_container, orient="vertical", command=lc.yview)
        lf = ttk.Frame(lc, style="Card.TFrame")
        
        lf.bind("<Configure>", lambda e: lc.configure(scrollregion=lc.bbox("all")))
        lc.create_window((0, 0), window=lf, anchor="nw")
        lc.configure(yscrollcommand=ls.set)
        
        lc.pack(side="left", fill="x", expand=True)
        ls.pack(side="right", fill="y")
        
        self.controller.scan_lang_vars = {}
        for l in avail:
            var = tk.BooleanVar(value=(l in last_used))
            self._create_check(lf, l, var)
            self.controller.scan_lang_vars[l] = var


    def refresh_languages(self):
        """Refresh the language list from available data packs."""
        self._build_language_checkboxes()
