import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import shutil
import time
import pikepdf
import os
import subprocess
import threading
import fitz  # PyMuPDF
from PIL import Image, ImageTk

# Local imports
from ..core.constants import APP_NAME, TEMP_DIR
from ..core.ocr_engine import detect_pdf_type, run_ocr, run_tesseract_export
from ..core.config_manager import state as app_state

# Import sv_ttk conditionally or manage theme manually
try:
    import sv_ttk
except ImportError:
    sv_ttk = None

class PDFViewer(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.doc = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom = 1.0
        self.image_ref = None

        # Mode: 'image' or 'text'
        self.view_mode = "image" 

        self.toolbar = ttk.Frame(self)
        self.toolbar.pack(side="top", fill="x", pady=2)
        
        self.btn_prev = ttk.Button(self.toolbar, text="<", command=self.prev_page, state="disabled", width=3)
        self.btn_prev.pack(side="left", padx=5)
        
        self.lbl_page = ttk.Label(self.toolbar, text="0 / 0")
        self.lbl_page.pack(side="left", padx=5)
        
        self.btn_next = ttk.Button(self.toolbar, text=">", command=self.next_page, state="disabled", width=3)
        self.btn_next.pack(side="left", padx=5)

        ttk.Separator(self.toolbar, orient="vertical").pack(side="left", fill="y", padx=10)

        self.btn_zoom_in = ttk.Button(self.toolbar, text="+", command=self.zoom_in, width=3)
        self.btn_zoom_in.pack(side="left")
        self.btn_zoom_out = ttk.Button(self.toolbar, text="-", command=self.zoom_out, width=3)
        self.btn_zoom_out.pack(side="left")
        
        # View Mode Toggle
        self.var_mode = tk.StringVar(value="image")
        ttk.Radiobutton(self.toolbar, text="Image", variable=self.var_mode, value="image", command=self.switch_mode).pack(side="right", padx=5)
        ttk.Radiobutton(self.toolbar, text="Text", variable=self.var_mode, value="text", command=self.switch_mode).pack(side="right", padx=5)

        # Content Area
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)
        
        # Canvas for Image
        self.canvas = tk.Canvas(self.container, bg="#333333", highlightthickness=0)
        self.scrollbar_y = ttk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        self.scrollbar_x = ttk.Scrollbar(self.container, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.scrollbar_y.set, xscrollcommand=self.scrollbar_x.set)
        
        # Text Widget for Text Mode
        self.text_view = tk.Text(self.container, wrap="word", font=("Segoe UI", 11), state="disabled")
        
        # Initial pack (Image mode by default)
        self.pack_view_mode()

    def pack_view_mode(self):
        # Clear current pack
        self.canvas.pack_forget()
        self.scrollbar_y.pack_forget()
        self.scrollbar_x.pack_forget()
        self.text_view.pack_forget()
        
        if self.view_mode == "image":
            self.scrollbar_y.pack(side="right", fill="y")
            self.scrollbar_x.pack(side="bottom", fill="x")
            self.canvas.pack(side="left", fill="both", expand=True)
        else:
            self.text_view.pack(fill="both", expand=True)
            
        self.show_page()

    def switch_mode(self):
        self.view_mode = self.var_mode.get()
        self.pack_view_mode()

    def load_pdf(self, path, password=None):
        try:
            self.doc = fitz.open(path)
            if self.doc.needs_pass:
                if password:
                    self.doc.authenticate(password)
                else:
                    return
            
            self.total_pages = len(self.doc)
            self.current_page = 0
            self.update_nav()
            self.show_page()
        except Exception as e:
            pass

    def update_nav(self):
        self.lbl_page.config(text=f"{self.current_page + 1} / {self.total_pages}")
        self.btn_prev.config(state="normal" if self.current_page > 0 else "disabled")
        self.btn_next.config(state="normal" if self.current_page < self.total_pages - 1 else "disabled")

    def show_page(self):
        if not self.doc: return
        
        page = self.doc.load_page(self.current_page)
        
        if self.view_mode == "image":
            # Image Render
            # Calculate zoom matrix
            mat = fitz.Matrix(self.zoom, self.zoom)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("ppm")
            self.image_ref = ImageTk.PhotoImage(data=img_data)
            
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, image=self.image_ref, anchor="nw")
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
            
        else:
            # Text Extraction
            text = page.get_text("text")
            self.text_view.config(state="normal")
            self.text_view.delete("1.0", "end")
            self.text_view.insert("1.0", text if text.strip() else "[No selectable text found on this page]")
            self.text_view.config(state="disabled")

    def next_page(self):
        if self.doc and self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_nav()
            self.show_page()

    def prev_page(self):
        if self.doc and self.current_page > 0:
            self.current_page -= 1
            self.update_nav()
            self.show_page()
            
    def zoom_in(self):
        self.zoom += 0.2
        self.show_page()

    def zoom_out(self):
        if self.zoom > 0.4:
            self.zoom -= 0.2
            self.show_page()


class BiplobOCR(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw() # Hide until setup done
        self.load_settings()
        
        self.title(app_state.t("app_title"))
        self.geometry("1100x750")
        
        self.build_ui()
        self.deiconify()

    def load_settings(self):
        # Apply theme
        theme = app_state.get("theme")
        if sv_ttk:
            if theme == "dark":
                sv_ttk.set_theme("dark")
            elif theme == "light":
                sv_ttk.set_theme("light")
            else:
                # For system, arguably use standard theme if sv_ttk forces one.
                # sv_ttk doesn't have a "system" mode exactly, it mimics win 11.
                # If user wants system native look, we might avoid sv_ttk. 
                # But let's assume they mean auto-detect light/dark.
                # Actually user said "I don't like design... I want mode: system". 
                # If they select 'system' and find sv_ttk intrusive, we might skip it.
                # BUT sv_ttk is the only way to get dark mode on win32 easily without custom drawing.
                # Let's try to just toggle the mode properly.
                try:
                    import darkdetect
                    is_dark = darkdetect.isDark()
                    sv_ttk.set_theme("dark" if is_dark else "light")
                except:
                    sv_ttk.set_theme("light") 

    def build_ui(self):
        # Top Menubar (for Settings)
        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)
        
        settings_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="⚙️ " + app_state.t("settings_title"), menu=settings_menu)
        
        # Language Submenu
        lang_menu = tk.Menu(settings_menu, tearoff=0)
        settings_menu.add_cascade(label=app_state.t("lbl_lang"), menu=lang_menu)
        lang_menu.add_command(label="English", command=lambda: self.change_lang("en"))
        lang_menu.add_command(label="বাংলা", command=lambda: self.change_lang("bn"))
        
        # Theme Submenu
        theme_menu = tk.Menu(settings_menu, tearoff=0)
        settings_menu.add_cascade(label=app_state.t("lbl_theme"), menu=theme_menu)
        theme_menu.add_command(label="Dark", command=lambda: self.change_theme("dark"))
        theme_menu.add_command(label="Light", command=lambda: self.change_theme("light"))
        theme_menu.add_command(label="System", command=lambda: self.change_theme("system"))

        # Main Layout
        self.paned = ttk.PanedWindow(self, orient="horizontal")
        self.paned.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Sidebar ---
        self.sidebar = ttk.Frame(self.paned, width=280, padding=15)
        self.paned.add(self.sidebar, weight=0)

        # Title
        ttk.Label(self.sidebar, text=app_state.t("app_title"), font=("Segoe UI Variable Display", 22, "bold")).pack(pady=(0, 20), anchor="w")
        
        # Open Button
        ttk.Button(self.sidebar, text=app_state.t("btn_open"), command=self.open_pdf, style="Accent.TButton").pack(fill="x", pady=5)
        
        # Options Group
        opt_frame = ttk.LabelFrame(self.sidebar, text=app_state.t("grp_options"), padding=10)
        opt_frame.pack(fill="x", pady=20)
        
        # Load Defaults from persistent state (defaulting to False as requested)
        self.var_deskew = tk.BooleanVar(value=app_state.get_option("deskew"))
        self.var_clean = tk.BooleanVar(value=app_state.get_option("clean"))
        self.var_rotate = tk.BooleanVar(value=app_state.get_option("rotate"))
        self.var_force = tk.BooleanVar(value=app_state.get_option("force"))
        self.var_optimize = tk.StringVar(value=app_state.get_option("optimize"))
        
        ttk.Checkbutton(opt_frame, text=app_state.t("opt_deskew"), variable=self.var_deskew).pack(anchor="w", pady=2)
        ttk.Checkbutton(opt_frame, text=app_state.t("opt_clean"), variable=self.var_clean).pack(anchor="w", pady=2)
        ttk.Checkbutton(opt_frame, text=app_state.t("opt_rotate"), variable=self.var_rotate).pack(anchor="w", pady=2)
        ttk.Checkbutton(opt_frame, text=app_state.t("opt_force"), variable=self.var_force).pack(anchor="w", pady=2)
        
        ttk.Label(opt_frame, text=app_state.t("lbl_optimize")).pack(anchor="w", pady=(10, 2))
        ttk.Combobox(opt_frame, textvariable=self.var_optimize, values=["0", "1", "2", "3"], state="readonly").pack(fill="x")

        # Process Button
        self.btn_process = ttk.Button(self.sidebar, text=app_state.t("btn_process"), command=self.start_processing_thread, state="disabled", style="Accent.TButton")
        self.btn_process.pack(fill="x", pady=20)
        
        # Status
        self.lbl_status = ttk.Label(self.sidebar, text=app_state.t("lbl_status_idle"), foreground="gray", wraplength=250)
        self.lbl_status.pack(anchor="w", pady=5)
        
        self.progress = ttk.Progressbar(self.sidebar, mode="indeterminate")
        self.progress.pack(fill="x", pady=5)

        # --- Content Area ---
        self.content_frame = ttk.Frame(self.paned)
        self.paned.add(self.content_frame, weight=1)
        
        # We use a container to swap between "Viewer" and "Success View"
        self.view_container = ttk.Frame(self.content_frame)
        self.view_container.pack(fill="both", expand=True)
        
        self.viewer = PDFViewer(self.view_container)
        self.viewer.pack(fill="both", expand=True)

        # Success View (Created but hidden)
        self.success_frame = ttk.Frame(self.content_frame)
        # We will pack this when needed by hiding view_container

    # --- Actions ---

    def change_lang(self, lang):
        app_state.save_config({"language": lang})
        self.reload_ui()

    def change_theme(self, theme):
        app_state.save_config({"theme": theme})
        if sv_ttk:
            if theme == "dark": sv_ttk.set_theme("dark")
            elif theme == "light": sv_ttk.set_theme("light")
            else: sv_ttk.set_theme("light") # Fallback for system if no detect
        self.reload_ui() # Only needed if text needs update

    def reload_ui(self):
        # Cheap reload: destroy and rebuild OR just restart app. 
        # Restart is safer for Tkinter translation updates.
        messagebox.showinfo("Restart Required", "Please restart the application to apply changes fully.")
        self.destroy()

    def open_pdf(self):
        pdf = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not pdf: return
        self.current_pdf_path = pdf
        
        # Determine password
        password = None
        try:
            with pikepdf.open(pdf): pass
        except pikepdf.PasswordError:
            password = simpledialog.askstring("Password", "Enter PDF Password:", show="*")
            if not password: return
        
        self.current_pdf_password = password
        self.viewer.load_pdf(pdf, password)
        self.btn_process.config(state="normal")
        
        # Show viewer, hide success if open
        self.success_frame.pack_forget()
        self.view_container.pack(fill="both", expand=True)
        self.lbl_status.config(text=f"Loaded: {os.path.basename(pdf)}")

    def start_processing_thread(self):
        # Save current options to state
        app_state.set_option("deskew", self.var_deskew.get())
        app_state.set_option("clean", self.var_clean.get())
        app_state.set_option("rotate", self.var_rotate.get())
        app_state.set_option("force", self.var_force.get())
        app_state.set_option("optimize", self.var_optimize.get())
        app_state.save_config({}) # Persist to disk

        self.btn_process.config(state="disabled")
        self.progress.start(10)
        self.lbl_status.config(text=app_state.t("lbl_status_processing"))
        
        thread = threading.Thread(target=self.run_process_logic)
        thread.daemon = True
        thread.start()

    def run_process_logic(self):
        try:
            opts = {
                "deskew": self.var_deskew.get(),
                "clean": self.var_clean.get(),
                "rotate": self.var_rotate.get(),
                "optimize": self.var_optimize.get(),
            }
            temp_out = os.path.join(TEMP_DIR, "processed_output.pdf")
            
            sidecar = run_ocr(
                self.current_pdf_path, 
                temp_out, 
                self.current_pdf_password, 
                self.var_force.get(),
                options=opts
            )
            self.after(0, lambda: self.on_process_success(temp_out, sidecar))
            
        except subprocess.CalledProcessError as e:
            err_text = str(e.stderr).lower() if e.stderr else ""
            if "priorocrfounderror" in err_text or "page already has text" in err_text:
                self.after(0, lambda: self.ask_force_continuation())
            else:
                self.after(0, lambda: self.on_process_fail(str(e.stderr)))
        except Exception as e:
            self.after(0, lambda: self.on_process_fail(str(e)))

    def on_process_fail(self, msg):
        self.progress.stop()
        self.btn_process.config(state="normal")
        self.lbl_status.config(text="Failed: " + msg[:30])
        messagebox.showerror("Error", msg)

    def ask_force_continuation(self):
        self.progress.stop()
        proceed = messagebox.askyesno("Text Detected", "Files already has text. Force OCR?")
        if proceed:
            self.var_force.set(True)
            self.start_processing_thread()
        else:
            self.on_process_fail("Aborted.")

    def on_process_success(self, temp_out, sidecar):
        self.progress.stop()
        self.btn_process.config(state="normal")
        self.lbl_status.config(text=app_state.t("lbl_status_done"))
        
        # Show Success UI in Center
        self.view_container.pack_forget()
        self.show_success_ui(temp_out, sidecar)

    def show_success_ui(self, temp_out, sidecar):
        # Clear previous
        for widget in self.success_frame.winfo_children():
            widget.destroy()
        
        self.success_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Center Content
        center = ttk.Frame(self.success_frame)
        center.place(relx=0.5, rely=0.5, anchor="center")
        
        ttk.Label(center, text="✅ " + app_state.t("msg_success"), font=("Segoe UI", 25)).pack(pady=20)
        ttk.Label(center, text=app_state.t("lbl_export_prompt"), font=("Segoe UI", 12)).pack(pady=10)
        
        btn_frame = ttk.Frame(center)
        btn_frame.pack(pady=20)
        
        # 1. Save PDF
        def save_pdf():
            f = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
            if f:
                shutil.copy(temp_out, f)
                messagebox.showinfo("Saved", f"PDF Saved to {f}")

        # 2. Save Text
        def save_txt():
            f = filedialog.asksaveasfilename(defaultextension=".txt")
            if f:
                shutil.copy(sidecar, f)
                messagebox.showinfo("Saved", "Text Saved.")

        # 3. Save hOCR
        def save_hocr():
            f = filedialog.asksaveasfilename(defaultextension=".hocr")
            if f:
                # Mock call or real call
                try:
                    run_tesseract_export(self.current_pdf_path, f.replace(".hocr", ""), "hocr")
                    messagebox.showinfo("Saved", "hOCR Saved.")
                except:
                    messagebox.showerror("Error", "Export failed.")

        ttk.Button(btn_frame, text="💾 Save Final PDF", command=save_pdf, style="Accent.TButton", width=25).pack(pady=5)
        ttk.Button(btn_frame, text="📄 " + app_state.t("btn_save_txt"), command=save_txt, width=25).pack(pady=5)
        ttk.Button(btn_frame, text="📑 " + app_state.t("btn_save_hocr"), command=save_hocr, width=25).pack(pady=5)
        
        ttk.Button(center, text=app_state.t("btn_close_export"), command=self.close_success_ui).pack(pady=20)

    def close_success_ui(self):
        self.success_frame.pack_forget()
        self.view_container.pack(fill="both", expand=True)

