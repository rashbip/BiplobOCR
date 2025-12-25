import tkinter as tk
from tkinter import ttk
from ..core.config_manager import state as app_state

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title(app_state.t("settings_title"))
        self.geometry("500x400")
        self.resizable(False, False)
        
        self.parent = parent
        self.transient(parent)
        self.grab_set()
        
        self.build_ui()
        
    def build_ui(self):
        container = ttk.Frame(self, padding=20)
        container.pack(fill="both", expand=True)
        
        notebook = ttk.Notebook(container)
        notebook.pack(fill="both", expand=True)
        
        # --- General Tab ---
        tab_general = ttk.Frame(notebook, padding=10)
        notebook.add(tab_general, text="General")
        
        # Language
        ttk.Label(tab_general, text=app_state.t("lbl_lang")).pack(anchor="w")
        self.var_lang = tk.StringVar(value=app_state.get("language", "en"))
        lang_cb = ttk.Combobox(tab_general, textvariable=self.var_lang, values=["en", "bn"], state="readonly")
        lang_cb.pack(fill="x", pady=(5, 15))
        
        # Theme
        ttk.Label(tab_general, text=app_state.t("lbl_theme")).pack(anchor="w")
        self.var_theme = tk.StringVar(value=app_state.get("theme", "system"))
        theme_cb = ttk.Combobox(tab_general, textvariable=self.var_theme, values=["system", "dark", "light"], state="readonly")
        theme_cb.pack(fill="x", pady=(5, 15))
        
        # --- Advanced Tab ---
        tab_adv = ttk.Frame(notebook, padding=10)
        notebook.add(tab_adv, text="Advanced")
        
        ttk.Label(tab_adv, text="Default export format:").pack(anchor="w")
        self.var_fmt = tk.StringVar(value="pdf") # Placeholder
        ttk.Combobox(tab_adv, textvariable=self.var_fmt, values=["pdf", "pdfa", "txt"], state="readonly").pack(fill="x", pady=5)
        
        ttk.Label(tab_adv, text="(More options can be added here)").pack(anchor="w", pady=20, foreground="gray")
        
        # --- Buttons ---
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill="x", pady=10)
        
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Save & Restart", style="Accent.TButton", command=self.save_settings).pack(side="right")
        
    def save_settings(self):
        # Save
        new_conf = {
            "language": self.var_lang.get(),
            "theme": self.var_theme.get()
        }
        app_state.save_config(new_conf)
        self.destroy()
        self.parent.reload_ui()
