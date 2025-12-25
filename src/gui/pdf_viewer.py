import tkinter as tk
from tkinter import ttk, messagebox, Menu, filedialog
import os

import fitz  # PyMuPDF
from PIL import Image, ImageTk
import math
from ..core.theme import MAIN_FONT, HEADER_FONT
from ..core import platform_utils
from ..core.emoji_label import EmojiLabel, render_emoji_image
from ..core.config_manager import state as app_state # Correct import


class PDFViewer(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.doc = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom = 1.0
        self.rotation = 0
        self.view_mode = "image" # Initialized view mode
        self.is_text_mode = False # Initialized text mode flag
        self.image_ref = None
        self.pdf_path = None
        
        # Canvas state for selection
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.selection_rect = None # (x0, y0, x1, y1) in image coords

        self.build_ui()

    def build_ui(self):
        # --- Top Toolbar ---
        self.toolbar = ttk.Frame(self, padding=5, style="Card.TFrame")
        self.toolbar.pack(side="top", fill="x")

        # Filename Label
        self.lbl_filename = EmojiLabel(self.toolbar, text="No File Open", font=(MAIN_FONT, 10, "bold"))
        self.lbl_filename.pack(side="left", padx=(5, 20))

        # Open File Button
        btn_open = ttk.Button(self.toolbar, command=self.open_file)
        # Using a direct call to the key if possible, or just the string
        img_open = render_emoji_image(app_state.t("btn_open_computer"), (MAIN_FONT, 10), "white", btn_open)
        if img_open:
            btn_open.config(image=img_open, text="")
            btn_open._img = img_open
        else:
            btn_open.config(text="📂 Open")
        btn_open.pack(side="left", padx=5)

        # Navigation
        btn_first = ttk.Button(self.toolbar, command=self.first_page, width=5)
        img_first = render_emoji_image("First", (MAIN_FONT, 10), "white", btn_first)
        if img_first: btn_first.config(image=img_first); btn_first._img=img_first
        else: btn_first.config(text="First")
        btn_first.pack(side="left", padx=1)

        btn_prev = ttk.Button(self.toolbar, command=self.prev_page, width=3)
        img_prev = render_emoji_image("<", (MAIN_FONT, 10), "white", btn_prev)
        if img_prev: btn_prev.config(image=img_prev); btn_prev._img=img_prev
        else: btn_prev.config(text="<")
        btn_prev.pack(side="left", padx=1)

        self.lbl_page = EmojiLabel(self.toolbar, text="0 / 0", font=(MAIN_FONT, 10))
        self.lbl_page.pack(side="left", padx=5)

        btn_next = ttk.Button(self.toolbar, command=self.next_page, width=3)
        img_next = render_emoji_image(">", (MAIN_FONT, 10), "white", btn_next)
        if img_next: btn_next.config(image=img_next); btn_next._img=img_next
        else: btn_next.config(text=">")
        btn_next.pack(side="left", padx=1)

        btn_last = ttk.Button(self.toolbar, command=self.last_page, width=5)
        img_last = render_emoji_image("Last", (MAIN_FONT, 10), "white", btn_last)
        if img_last: btn_last.config(image=img_last); btn_last._img=img_last
        else: btn_last.config(text="Last")
        btn_last.pack(side="left", padx=1)

        
        ttk.Separator(self.toolbar, orient="vertical").pack(side="left", fill="y", padx=10)

        # Zoom
        btn_zout = ttk.Button(self.toolbar, command=self.zoom_out, width=3)
        img_zout = render_emoji_image("-", (MAIN_FONT, 10), "white", btn_zout)
        if img_zout: btn_zout.config(image=img_zout); btn_zout._img=img_zout
        else: btn_zout.config(text="-")
        btn_zout.pack(side="left")

        self.lbl_zoom = EmojiLabel(self.toolbar, text="100%", font=(MAIN_FONT, 10))
        self.lbl_zoom.pack(side="left", padx=2)

        btn_zin = ttk.Button(self.toolbar, command=self.zoom_in, width=3)
        img_zin = render_emoji_image("+", (MAIN_FONT, 10), "white", btn_zin)
        if img_zin: btn_zin.config(image=img_zin); btn_zin._img=img_zin
        else: btn_zin.config(text="+")
        btn_zin.pack(side="left")

        
        ttk.Separator(self.toolbar, orient="vertical").pack(side="left", fill="y", padx=10)
        
        # Tools
        btn_rot = ttk.Button(self.toolbar, command=self.rotate_view)
        img_rot = render_emoji_image("Rotate", (MAIN_FONT, 10), "white", btn_rot)
        if img_rot: btn_rot.config(image=img_rot); btn_rot._img=img_rot
        else: btn_rot.config(text="Rotate")
        btn_rot.pack(side="left", padx=2)

        
        # View Mode Switch (Icon-like)
        self.is_text_mode = False
        self.btn_mode = ttk.Button(self.toolbar, command=self.toggle_view_mode)
        self._update_mode_button_text()

        self.btn_mode.pack(side="right", padx=10)

        # --- Main Container Stack ---
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)

        # 1. Canvas View (Image)
        self.canvas_frame = ttk.Frame(self.container)
        self.canvas = tk.Canvas(self.canvas_frame, bg="#2b2b2b", highlightthickness=0)
        self.v_scroll = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.h_scroll = ttk.Scrollbar(self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        
        self.v_scroll.pack(side="right", fill="y")
        self.h_scroll.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

        # 2. Text View (Raw Text)
        self.text_frame = ttk.Frame(self.container)
        self.text_widget = tk.Text(self.text_frame, wrap="word", font=(MAIN_FONT, 11), padx=20, pady=20)
        self.text_scroll = ttk.Scrollbar(self.text_frame, orient="vertical", command=self.text_widget.yview)
        self.text_widget.config(yscrollcommand=self.text_scroll.set)
        
        self.text_scroll.pack(side="right", fill="y")
        self.text_widget.pack(side="left", fill="both", expand=True)

        # Events
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)

        # Show initial
        self.canvas_frame.pack(fill="both", expand=True)

    def _update_mode_button_text(self):
        txt = "🖼 View Image" if self.is_text_mode else "👁 View Text"
        img = render_emoji_image(txt, (MAIN_FONT, 9), "white", self.btn_mode)

        if img:
            self.btn_mode.config(image=img, text="")
            self.btn_mode._img = img
        else:
            self.btn_mode.config(text=platform_utils.sanitize_for_linux(txt))

    def toggle_view_mode(self):
        self.is_text_mode = not self.is_text_mode
        self.view_mode = "text" if self.is_text_mode else "image"
        self._update_mode_button_text()

        
        if self.view_mode == "text":
            self.canvas_frame.pack_forget()
            self.text_frame.pack(fill="both", expand=True)
            self.show_text_content()
        else:
            self.text_frame.pack_forget()
            self.canvas_frame.pack(fill="both", expand=True)
            # Image is already there or needs refresh?
            # It persists, so no need to reload unless page changed.

    def show_text_content(self):
        if not self.doc: return
        page = self.doc.load_page(self.current_page)
        text = page.get_text("text")
        
        self.text_widget.config(state="normal")
        self.text_widget.delete("1.0", "end")
        self.text_widget.insert("1.0", text if text.strip() else "[No text layer found on this page]")
        self.text_widget.config(state="disabled")

    def show_page(self):
        if not self.doc: return
        self.canvas.delete("all")
        
        page = self.doc.load_page(self.current_page)
        if self.rotation != 0:
            page.set_rotation(self.rotation)
            
        mat = fitz.Matrix(self.zoom, self.zoom)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("ppm")
        
        self.image_ref = ImageTk.PhotoImage(data=img_data)
        
        # Center image logic optional, but simple placement:
        self.canvas.create_image(0, 0, image=self.image_ref, anchor="nw")
        
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        # If text mode is active, also update text
        if self.is_text_mode:
            self.show_text_content()

    def load_pdf(self, path, password=None):
        try:
            self.pdf_path = path
            self.doc = fitz.open(path)
            if self.doc.needs_pass:
                if password:
                    self.doc.authenticate(password)
                else:
                    messagebox.showerror("Error", "Password required")
                    return
            
            self.total_pages = len(self.doc)
            self.current_page = 0
            self.rotation = 0
            self.lbl_filename.set_text(os.path.basename(path))
            self.show_page()
            self.update_ui_state()
        except Exception as e:
            messagebox.showerror("Error loading PDF", str(e))

    def update_ui_state(self):
        self.lbl_filename.set_text(os.path.basename(self.pdf_path) if self.pdf_path else "No File Open")
        self.lbl_page.config(text=f"{self.current_page + 1} / {self.total_pages}")
        self.lbl_zoom.config(text=f"{int(self.zoom * 100)}%")

    def open_file(self):
        f = None
        if platform_utils.IS_LINUX:
            f = platform_utils.linux_file_dialog(
                title="Select PDF",
                initialdir=app_state.get_initial_dir(),
                filetypes=[("PDF Files", "*.pdf")]
            )
        else:
            f = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])

        if f:
            if platform_utils.IS_LINUX:
                app_state.save_config({"last_open_dir": os.path.dirname(f)})
            self.load_pdf(f)





    # Navigation
    def next_page(self):
        if self.doc and self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.show_page()
            self.update_ui_state()

    def prev_page(self):
        if self.doc and self.current_page > 0:
            self.current_page -= 1
            self.show_page()
            self.update_ui_state()
            
    def first_page(self):
        if self.doc:
            self.current_page = 0
            self.show_page()
            self.update_ui_state()

    def last_page(self):
        if self.doc:
            self.current_page = self.total_pages - 1
            self.show_page()
            self.update_ui_state()

    def zoom_in(self):
        self.zoom += 0.25
        self.show_page()
        self.update_ui_state()

    def zoom_out(self):
        if self.zoom > 0.3:
            self.zoom -= 0.25
            self.show_page()
            self.update_ui_state()
            
    def rotate_view(self):
        self.rotation = (self.rotation + 90) % 360
        self.show_page()

    # --- Interaction (Text Selection) ---
    def on_mouse_down(self, event):
        if not self.doc: return
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None

    def on_mouse_drag(self, event):
        if not self.doc: return
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        
        if self.rect_id:
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)
        else:
            self.rect_id = self.canvas.create_rectangle(
                self.start_x, self.start_y, cur_x, cur_y,
                outline="#007acc", fill="#007acc", stipple="gray25", width=2
            )

    def on_mouse_up(self, event):
        if not self.doc or not self.rect_id: return
        
        x1, y1, x2, y2 = self.canvas.coords(self.rect_id)
        
        # Normalize
        r = fitz.Rect(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        
        # Convert Canvas Coords -> PDF Coords
        # PDF Coords = Canvas Coords / Zoom
        pdf_rect = r / self.zoom
        
        # Extract Text
        try:
            page = self.doc.load_page(self.current_page)
            if self.rotation != 0:
                page.set_rotation(self.rotation)
                # Note: Coordinates might be tricky with rotation, fitz usually handles cropbox but let's see.
            
            text = page.get_text("text", clip=pdf_rect)
            if text.strip():
                self.show_selection_menu(event, text.strip())
            else:
                pass # No text found (maybe image)
        except Exception as e:
            print(e)
            
    def show_selection_menu(self, event, text):
        menu = Menu(self, tearoff=0)
        menu.add_command(label="Copy Text", command=lambda: self.copy_to_clipboard(text))
        menu.add_separator()
        menu.add_command(label=f"Text found: {text[:20]}...", state="disabled")
        menu.tk_popup(event.x_root, event.y_root)

    def copy_to_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Copied", "Text copied to clipboard!")
        
    def on_mouse_wheel(self, event):
        # Basic scroll support
        if self.doc:
           # Windows: event.delta, Linux: event.num
           if event.delta:
               self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
