import tkinter as tk
from tkinter import ttk
from tkinterdnd2 import DND_FILES
from ...core.theme import SURFACE_COLOR, THEME_COLOR, MAIN_FONT, HEADER_FONT
from ...core.config_manager import state as app_state
from ...core.emoji_label import EmojiLabel, render_emoji_image


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
        # Main layout: Sidebar (Options) + Main (List)
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # --- Sidebar (Options) ---
        self.sidebar = ttk.Frame(paned, width=300, padding=(0, 0, 10, 0))
        paned.add(self.sidebar, weight=0)
        
        EmojiLabel(self.sidebar, text=app_state.t("lbl_batch_opts"), font=(HEADER_FONT, 20, "bold"), foreground=THEME_COLOR).pack(anchor="w", pady=(20, 10))

        
        # Options Group
        opt_group = ttk.Frame(self.sidebar, padding=10, style="Card.TFrame")
        opt_group.pack(fill="x", pady=5)
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

        ttk.Combobox(opt_group, textvariable=self.controller.var_optimize, values=["0", "1", "2", "3"], state="readonly").pack(fill="x")


        # Languages Group
        lang_group = ttk.Frame(self.sidebar, padding=10, style="Card.TFrame")
        lang_group.pack(fill="x", pady=15)
        EmojiLabel(lang_group, text="Processing Languages", font=(MAIN_FONT, 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        # Container for dynamic language list
        self.lang_container = ttk.Frame(lang_group)

        self.lang_container.pack(fill="x", expand=True)
        
        # Build initial language list
        self._build_language_checkboxes()

        # Action Button (Start)
        self.controller.btn_start_batch = ttk.Button(self.sidebar, command=self.controller.start_batch_processing, style="Accent.TButton")
        img_start = render_emoji_image(app_state.t("btn_start_batch", sanitize=False), (MAIN_FONT, 18), "white", self.controller.btn_start_batch)
        if img_start:
            self.controller.btn_start_batch.config(image=img_start, text="")
            self.controller.btn_start_batch._img = img_start
        else:
            self.controller.btn_start_batch.config(text=app_state.t("btn_start_batch", sanitize=False))


        self.controller.btn_start_batch.pack(fill="x", pady=20)



        # --- Main Content (File List) ---
        main_content = ttk.Frame(paned, padding=(10, 0, 0, 0))
        paned.add(main_content, weight=1)

        EmojiLabel(main_content, text=app_state.t("batch_title"), font=(HEADER_FONT, 20, "bold"), foreground=THEME_COLOR).pack(anchor="w", pady=(20, 10))
        EmojiLabel(main_content, text=app_state.t("batch_desc"), font=(MAIN_FONT, 14), foreground="gray").pack(anchor="w", pady=(0, 20))

        
        toolbar = ttk.Frame(main_content)
        toolbar.pack(fill="x", pady=5)
        btn_add = ttk.Button(toolbar, command=self.controller.add_batch_files, style="Accent.TButton", width=15)
        img_add = render_emoji_image(app_state.t("btn_add_files", sanitize=False), (MAIN_FONT, 18), "white", btn_add)
        if img_add:
            btn_add.config(image=img_add, text="")
            btn_add._img = img_add
        else:
            btn_add.config(text=app_state.t("btn_add_files", sanitize=False))


        btn_add.pack(side="left", padx=(0, 5))

        btn_clear = ttk.Button(toolbar, command=self.controller.clear_batch_files)
        img_clear = render_emoji_image(app_state.t("btn_clear_list"), (MAIN_FONT, 18), "white", btn_clear)
        if img_clear:
            btn_clear.config(image=img_clear, text="")
            btn_clear._img = img_clear
        else:
            btn_clear.config(text=app_state.t("btn_clear_list"))

        btn_clear.pack(side="left", padx=(0, 5))



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
            self._create_check(lf, l, var)
            self.controller.batch_lang_vars[l] = var


    def refresh_languages(self):
        """Refresh the language list from available data packs."""
        self._build_language_checkboxes()
