import tkinter as tk
from tkinter import ttk
from tkinterdnd2 import DND_FILES
from ...core.theme import SURFACE_COLOR, THEME_COLOR
from ...core.config_manager import state as app_state

class BatchView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=40)
        self.controller = controller
        
        self.build_ui()
        
        # Drag & Drop Registration
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.on_drop)

    def on_drop(self, event):
        if event.data:
            self.controller.add_dropped_batch_files(event.data)

    def build_ui(self):
        # Main layout: Sidebar (Options) + Main (List)
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # --- Sidebar (Options) ---
        self.sidebar = ttk.Frame(paned, width=300, padding=(0, 0, 10, 0))
        paned.add(self.sidebar, weight=0)
        
        ttk.Label(self.sidebar, text=app_state.t("lbl_batch_opts"), style="Header.TLabel").pack(anchor="w", pady=(20, 10))
        
        # Options Group
        opt_frame = ttk.LabelFrame(self.sidebar, text=app_state.t("grp_options"), padding=10)
        opt_frame.pack(fill="x", pady=5)
        ttk.Checkbutton(opt_frame, text=app_state.t("opt_deskew"), variable=self.controller.var_deskew).pack(anchor="w", pady=2)
        ttk.Checkbutton(opt_frame, text=app_state.t("opt_clean"), variable=self.controller.var_clean).pack(anchor="w", pady=2)
        ttk.Checkbutton(opt_frame, text=app_state.t("opt_rotate"), variable=self.controller.var_rotate).pack(anchor="w", pady=2)
        ttk.Checkbutton(opt_frame, text=app_state.t("opt_force"), variable=self.controller.var_force).pack(anchor="w", pady=2)
        ttk.Checkbutton(opt_frame, text=app_state.t("opt_rasterize"), variable=self.controller.var_rasterize).pack(anchor="w", pady=2)
        
        dpi_frame = ttk.Frame(opt_frame)
        dpi_frame.pack(fill="x", pady=5)
        ttk.Label(dpi_frame, text=app_state.t("lbl_dpi")).pack(side="left")
        ttk.Entry(dpi_frame, textvariable=self.controller.var_dpi, width=8).pack(side="right")

        ttk.Label(opt_frame, text=app_state.t("lbl_optimize")).pack(anchor="w", pady=(10, 2))
        ttk.Combobox(opt_frame, textvariable=self.controller.var_optimize, values=["0", "1", "2", "3"], state="readonly").pack(fill="x")

        # Languages Group
        self.lang_frame = ttk.LabelFrame(self.sidebar, text="Processing Languages", padding=10)
        self.lang_frame.pack(fill="x", pady=15)
        
        # Container for dynamic language list
        self.lang_container = ttk.Frame(self.lang_frame)
        self.lang_container.pack(fill="x", expand=True)
        
        # Build initial language list
        self._build_language_checkboxes()

        # Action Button (Start)
        self.controller.btn_start_batch = ttk.Button(self.sidebar, text=app_state.t("btn_start_batch"), command=self.controller.start_batch_processing, style="Accent.TButton")
        self.controller.btn_start_batch.pack(fill="x", pady=20)


        # --- Main Content (File List) ---
        main_content = ttk.Frame(paned, padding=(10, 0, 0, 0))
        paned.add(main_content, weight=1)

        ttk.Label(main_content, text=app_state.t("batch_title"), style="Header.TLabel").pack(anchor="w", pady=(20, 10))
        ttk.Label(main_content, text=app_state.t("batch_desc"), foreground="gray").pack(anchor="w", pady=(0, 20))
        
        toolbar = ttk.Frame(main_content)
        toolbar.pack(fill="x", pady=5)
        ttk.Button(toolbar, text=app_state.t("btn_add_files"), command=self.controller.add_batch_files, style="Accent.TButton", width=15).pack(side="left", padx=(0, 5))
        ttk.Button(toolbar, text=app_state.t("btn_clear_list"), command=self.controller.clear_batch_files).pack(side="left")

        cols = ("Filename", "Status")
        self.controller.batch_tree = ttk.Treeview(main_content, columns=cols, show="headings")
        self.controller.batch_tree.pack(fill="both", expand=True, pady=10)
        self.controller.batch_tree.heading("Filename", text=app_state.t("col_filename"))
        self.controller.batch_tree.heading("Status", text=app_state.t("col_status"))
        self.controller.batch_tree.column("Filename", width=400)
        self.controller.batch_tree.column("Status", width=150)

    def _build_language_checkboxes(self):
        """Build or rebuild the language checkboxes."""
        # Clear existing
        for widget in self.lang_container.winfo_children():
            widget.destroy()
        
        # Load available and previously selected
        from ...core.ocr_engine import get_available_languages
        avail = get_available_languages()
        last_used = app_state.get("last_used_ocr_languages")
        if not last_used:
            last_used = [app_state.get("ocr_language", "eng")]

        lc = tk.Canvas(self.lang_container, bg=SURFACE_COLOR, highlightthickness=0, height=150)
        ls = ttk.Scrollbar(self.lang_container, orient="vertical", command=lc.yview)
        lf = ttk.Frame(lc, style="Card.TFrame")
        
        lf.bind("<Configure>", lambda e: lc.configure(scrollregion=lc.bbox("all")))
        lc.create_window((0, 0), window=lf, anchor="nw")
        lc.configure(yscrollcommand=ls.set)
        
        lc.pack(side="left", fill="x", expand=True)
        ls.pack(side="right", fill="y")
        
        self.controller.batch_lang_vars = {}
        for l in avail:
            var = tk.BooleanVar(value=(l in last_used))
            ttk.Checkbutton(lf, text=l, variable=var).pack(anchor="w")
            self.controller.batch_lang_vars[l] = var

    def refresh_languages(self):
        """Refresh the language list from available data packs."""
        self._build_language_checkboxes()
