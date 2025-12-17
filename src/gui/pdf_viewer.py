import tkinter as tk
from tkinter import ttk, messagebox, Menu
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import math

class PDFViewer(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.doc = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom = 1.0
        self.rotation = 0
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
        self.lbl_filename = ttk.Label(self.toolbar, text="No File Open", font=("Segoe UI", 10, "bold"))
        self.lbl_filename.pack(side="left", padx=(5, 20))

        # Navigation
        ttk.Button(self.toolbar, text="First", command=self.first_page, width=4).pack(side="left", padx=1)
        ttk.Button(self.toolbar, text="<", command=self.prev_page, width=3).pack(side="left", padx=1)
        self.lbl_page = ttk.Label(self.toolbar, text="0 / 0", width=10, anchor="center")
        self.lbl_page.pack(side="left", padx=5)
        ttk.Button(self.toolbar, text=">", command=self.next_page, width=3).pack(side="left", padx=1)
        ttk.Button(self.toolbar, text="Last", command=self.last_page, width=4).pack(side="left", padx=1)
        
        ttk.Separator(self.toolbar, orient="vertical").pack(side="left", fill="y", padx=10)

        # Zoom
        ttk.Button(self.toolbar, text="-", command=self.zoom_out, width=3).pack(side="left")
        self.lbl_zoom = ttk.Label(self.toolbar, text="100%", width=6, anchor="center")
        self.lbl_zoom.pack(side="left", padx=2)
        ttk.Button(self.toolbar, text="+", command=self.zoom_in, width=3).pack(side="left")
        
        ttk.Separator(self.toolbar, orient="vertical").pack(side="left", fill="y", padx=10)
        
        # Additional Tools
        ttk.Button(self.toolbar, text="Of Rotate", command=self.rotate_view).pack(side="left", padx=2)
        
        # Mode info
        ttk.Label(self.toolbar, text="(Drag to Select Text)", foreground="gray").pack(side="right", padx=10)

        # --- Main Canvas ---
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.container, bg="#2b2b2b", highlightthickness=0)
        self.v_scroll = ttk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        self.h_scroll = ttk.Scrollbar(self.container, orient="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        
        self.v_scroll.pack(side="right", fill="y")
        self.h_scroll.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Events
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        # Mouse wheel
        self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)

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
            self.lbl_filename.config(text=path.split("/")[-1].split("\\")[-1])
            self.show_page()
            self.update_ui_state()
        except Exception as e:
            messagebox.showerror("Error loading PDF", str(e))

    def update_ui_state(self):
        self.lbl_page.config(text=f"{self.current_page + 1} / {self.total_pages}")
        self.lbl_zoom.config(text=f"{int(self.zoom * 100)}%")

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
        
        # Center or Top-Left? Standard is centered if smaller, topleft if larger.
        # We'll just put it at 0,0 and let scroll region handle it.
        self.canvas.create_image(0, 0, image=self.image_ref, anchor="nw")
        
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

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
