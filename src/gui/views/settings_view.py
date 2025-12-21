"""
Settings View - Application settings panel with data pack management.
Extracted from app.py for better maintainability.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil

from ...core.theme import BG_COLOR, SURFACE_COLOR, FG_COLOR, THEME_COLOR, MAIN_FONT, HEADER_FONT
from ...core.config_manager import state as app_state
from ...core.ocr_engine import get_available_languages, get_tessdata_dir


class SettingsView(ttk.Frame):
    """Settings panel view."""
    
    def __init__(self, parent, controller):
        super().__init__(parent, padding=40)
        self.controller = controller
        self.avail_langs = []
        self.build_ui()
    
    def build_ui(self):
        """Build the settings view UI."""
        # Create Scrollable Container
        canvas = tk.Canvas(self, bg=BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.settings_scroll_frame = ttk.Frame(canvas)
        
        self.settings_scroll_frame.bind("<Configure>", 
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        window_id = canvas.create_window((0, 0), window=self.settings_scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Ensure full width
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(window_id, width=e.width))
        
        # Enable Mousewheel Scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Build UI into settings_scroll_frame
        lbl = ttk.Label(self.settings_scroll_frame, text=app_state.t("settings_title"), 
                        font=(HEADER_FONT, 20, "bold"))
        lbl.pack(anchor="w", pady=(0, 20))
        
        # Hardware Config
        f_hw = ttk.LabelFrame(self.settings_scroll_frame, text=app_state.t("lbl_hw_settings"), padding=20)
        f_hw.pack(fill="x", pady=10)
        
        # GPU Selection
        ttk.Label(f_hw, text=app_state.t("lbl_dev_select")).pack(anchor="w")
        gpu_vals = ["Auto"] + self.controller.available_gpus
        self.cb_gpu = ttk.Combobox(f_hw, textvariable=self.controller.var_gpu_device, 
                                    values=gpu_vals, state="readonly")
        self.cb_gpu.pack(fill="x", pady=(5, 10))
        
        ttk.Checkbutton(f_hw, text=app_state.t("lbl_gpu"), 
                        variable=self.controller.var_gpu).pack(anchor="w")
        
        # Threads
        ttk.Label(f_hw, text=f"{app_state.t('lbl_threads')} (Total Cores: {self.controller.cpu_count})").pack(
            anchor="w", pady=(10, 0))
        ttk.Label(f_hw, text="Lower this value if your PC freezes.", 
                  foreground="gray", font=(MAIN_FONT, 8)).pack(anchor="w")
        
        # Scale for threads
        self.s_threads = tk.Scale(f_hw, from_=1, to=self.controller.cpu_count, orient="horizontal", 
                                   variable=self.controller.var_cpu_threads, background=SURFACE_COLOR, 
                                   foreground=FG_COLOR, highlightthickness=0)
        self.s_threads.pack(fill="x", pady=5)
        
        # Lang
        f_lang = ttk.LabelFrame(self.settings_scroll_frame, text=app_state.t("lbl_lang"), padding=20)
        f_lang.pack(fill="x", pady=10)
        
        # 1. Interface Language
        ttk.Label(f_lang, text=app_state.t("lbl_lang")).pack(anchor="w")
        self.cb_lang = ttk.Combobox(f_lang, textvariable=self.controller.var_lang, 
                                     values=["en", "bn"], state="readonly")
        self.cb_lang.pack(fill="x", pady=(5, 15))
        
        # 2. OCR Language
        self.avail_langs = get_available_languages()
        
        ttk.Label(f_lang, text=app_state.t("lbl_ocr_lang")).pack(anchor="w")
        self.controller.var_ocr_lang = tk.StringVar(value=app_state.get("ocr_language", "eng"))
        
        self.cb_ocr_lang = ttk.Combobox(f_lang, textvariable=self.controller.var_ocr_lang, 
                                         values=self.avail_langs, state="readonly")
        self.cb_ocr_lang.pack(fill="x", pady=5)
        
        # Data Packs Management
        ttk.Label(f_lang, text="Installed Data Packs", 
                  font=(MAIN_FONT, 9, "bold")).pack(anchor="w", pady=(15, 5))
        
        # Scrollable Container for Packs
        pack_container = ttk.Frame(f_lang, style="Card.TFrame", padding=2)
        pack_container.pack(fill="x", ipady=5)
        
        self.packs_canvas = tk.Canvas(pack_container, bg=BG_COLOR, height=150, highlightthickness=0)
        self.packs_scrollbar = ttk.Scrollbar(pack_container, orient="vertical", 
                                              command=self.packs_canvas.yview)
        self.packs_scroll_frame = ttk.Frame(self.packs_canvas, style="Card.TFrame")
        
        self.packs_scroll_frame.bind("<Configure>", 
            lambda e: self.packs_canvas.configure(scrollregion=self.packs_canvas.bbox("all")))
        self.packs_window = self.packs_canvas.create_window((0, 0), window=self.packs_scroll_frame, anchor="nw")
        self.packs_canvas.configure(yscrollcommand=self.packs_scrollbar.set)
        
        self.packs_canvas.pack(side="left", fill="both", expand=True)
        self.packs_scrollbar.pack(side="right", fill="y")
        self.packs_canvas.bind('<Configure>', 
            lambda e: self.packs_canvas.itemconfig(self.packs_window, width=e.width))

        btn_add_pack = ttk.Button(f_lang, text="➕ Add Data Pack", command=self.add_data_pack)
        btn_add_pack.pack(anchor="e", pady=5)
        
        self.refresh_data_packs_ui()
        
        # Save Trigger
        self.cb_lang.bind("<<ComboboxSelected>>", lambda e: self.controller.save_settings_inline())
        self.cb_ocr_lang.bind("<<ComboboxSelected>>", lambda e: self.controller.save_settings_inline())
        self.cb_gpu.bind("<<ComboboxSelected>>", lambda e: self.controller.save_settings_inline())
        self.s_threads.bind("<ButtonRelease-1>", lambda e: self.controller.save_settings_inline())
        
        # Danger Zone
        ttk.Separator(self.settings_scroll_frame, orient="horizontal").pack(fill="x", pady=30)
        
        f_danger = ttk.LabelFrame(self.settings_scroll_frame, text="Danger Zone", padding=20)
        f_danger.pack(fill="x", pady=(0, 20))
        
        ttk.Label(f_danger, text="Reset application to factory defaults. This cannot be undone.", 
                  foreground="#ff5555").pack(anchor="w")
        ttk.Button(f_danger, text="⚠ Factory Reset", style="Danger.TButton", 
                   command=self.factory_reset).pack(anchor="w", pady=(10, 0))

    def factory_reset(self):
        """Reset application to factory defaults."""
        print("Factory reset triggered")
        if messagebox.askyesno("Factory Reset", "Are you sure you want to reset all settings and data?"):
            try:
                if os.path.exists("config.json"):
                    os.remove("config.json")
                if os.path.exists("history.json"):
                    os.remove("history.json")
                
                messagebox.showinfo("Reset Complete", "Application will now restart.")
                self.controller.restart_application(force=True)
                
            except Exception as e:
                messagebox.showerror("Error", f"Reset failed: {e}")

    def _refresh_all_language_lists(self):
        """Refresh language lists in all views after data pack changes."""
        # Refresh this view
        self.refresh_data_packs_ui()
        self.refresh_ocr_languages()
        
        # Refresh scan view if exists
        if hasattr(self.controller, 'view_scan') and self.controller.view_scan:
            try:
                self.controller.view_scan.refresh_languages()
            except Exception:
                pass
        
        # Refresh batch view if exists
        if hasattr(self.controller, 'view_batch') and self.controller.view_batch:
            try:
                self.controller.view_batch.refresh_languages()
            except Exception:
                pass

    def refresh_ocr_languages(self):
        """Refresh the OCR language dropdown with available data packs."""
        self.avail_langs = get_available_languages()
        self.cb_ocr_lang['values'] = self.avail_langs
        
        # If current selection is not in available, reset to first available
        current = self.controller.var_ocr_lang.get()
        if current not in self.avail_langs and self.avail_langs:
            self.controller.var_ocr_lang.set(self.avail_langs[0])

    def refresh_data_packs_ui(self):
        """Refresh the data packs list UI."""
        for w in self.packs_scroll_frame.winfo_children():
            w.destroy()
        
        d = get_tessdata_dir()
        if not os.path.exists(d):
            return
        
        files = sorted([f for f in os.listdir(d) if "traineddata" in f])
        
        for f in files:
            is_disabled = f.endswith(".disabled")
            clean_name = f.replace(".disabled", "")
            
            row = ttk.Frame(self.packs_scroll_frame, padding=5)
            row.pack(fill="x", pady=1)
            
            # Icon/Name
            icon = "🔴" if is_disabled else "🟢"
            lbl = ttk.Label(row, text=f"{icon} {clean_name}", font=(MAIN_FONT, 9))
            if is_disabled:
                lbl.config(foreground="gray")
            lbl.pack(side="left", padx=5)
            
            # Actions - Protect OSD
            if clean_name == "osd.traineddata":
                ttk.Label(row, text="(System)", font=(MAIN_FONT, 8), 
                          foreground="gray").pack(side="right", padx=10)
                continue
            
            # Create closures properly
            def make_toggle_handler(fname, disabled):
                def toggle_disable():
                    src = os.path.join(d, fname)
                    if disabled:
                        dst = os.path.join(d, fname.replace(".disabled", ""))
                    else:
                        dst = os.path.join(d, fname + ".disabled")
                    try:
                        os.rename(src, dst)
                        self._refresh_all_language_lists()
                    except Exception as e:
                        messagebox.showerror("Error", str(e))
                return toggle_disable

            def make_delete_handler(fname):
                def delete_pack():
                    if messagebox.askyesno("Confirm", f"Delete {fname}?"):
                        try:
                            os.remove(os.path.join(d, fname))
                            self._refresh_all_language_lists()
                        except Exception as e:
                            messagebox.showerror("Error", str(e))
                return delete_pack

            btn_del = ttk.Button(row, text="🗑", width=3, 
                                  command=make_delete_handler(f), style="Danger.TButton")
            btn_del.pack(side="right", padx=2)
            
            btn_toggle = ttk.Button(row, text="Enable" if is_disabled else "Disable", 
                                     width=8, command=make_toggle_handler(f, is_disabled))
            btn_toggle.pack(side="right", padx=2)

    def add_data_pack(self):
        """Add a new Tesseract data pack."""
        f = filedialog.askopenfilename(title="Select Tesseract Data File", 
                                        filetypes=[("Trained Data", "*.traineddata")])
        if not f:
            return
        
        try:
            # Basic Validation
            with open(f, 'rb') as tf:
                header = tf.read(15)
                if len(header) < 10:
                    raise Exception("Invalid file content")
            
            dest = os.path.join(get_tessdata_dir(), os.path.basename(f))
            shutil.copy(f, dest)
            
            messagebox.showinfo("Success", f"Installed {os.path.basename(f)}")
            
            # Refresh Lists
            self._refresh_all_language_lists()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to install data pack: {e}")
