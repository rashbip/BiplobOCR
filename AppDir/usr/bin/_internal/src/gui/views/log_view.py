import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import fitz
from ...core.theme import MAIN_FONT

class LogView(tk.Toplevel):
    def __init__(self, parent, title="Process Details"):
        super().__init__(parent)
        self.title(title)
        self.geometry("1200x800")
        
        # Split: Left (Image) | Right (Log)
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left: Image Viewer - Prioritize Width
        self.frame_img = ttk.LabelFrame(paned, text="Processing Page", padding=0, width=900)
        paned.add(self.frame_img, weight=5) 
        
        self.lbl_img = ttk.Label(self.frame_img, text="Waiting...", anchor="center")
        self.lbl_img.pack(fill="both", expand=True, padx=5, pady=5)

        
        # Right: Log/Text
        self.frame_log = ttk.LabelFrame(paned, text="Live Log", padding=5, width=300)
        paned.add(self.frame_log, weight=2)
        
        self.txt_log = tk.Text(self.frame_log, background="#1e1e1e", foreground="#d4d4d4", font=("Consolas", 9), state="disabled", wrap="word")
        self.txt_log.pack(side="left", fill="both", expand=True)
        
        scroll = ttk.Scrollbar(self.frame_log, command=self.txt_log.yview)
        scroll.pack(side="right", fill="y")
        self.txt_log.config(yscrollcommand=scroll.set)
        
        # State
        self.raw_image = None
        self.current_img = None
        
        # Bind resize event
        self.frame_img.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        if self.raw_image:
            self.display_image()

    def update_image(self, pdf_path, page_num):
        """Renders the specific page from the PDF and displays it."""
        try:
            from ...core.platform_utils import to_linux_path
            linux_path = to_linux_path(pdf_path)
            
            # Ensure path exists
            import os
            if not os.path.exists(linux_path):
                self.append_log(f"Warning: PDF path not found for preview: {linux_path}")
                return

            doc = fitz.open(linux_path)
            if page_num < 0 or page_num >= len(doc):
                doc.close()
                return
            
            page = doc[page_num]
            # Render at moderate DPI for speed/quality balance
            pix = page.get_pixmap(dpi=150) 
            self.raw_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            doc.close()
            
            self.display_image()
            self.update_idletasks() # Force UI update
            
        except Exception as e:
            self.append_log(f"Error rendering page preview: {e}")
            import traceback
            traceback.print_exc()
            
    def display_image(self):
        if not self.raw_image: return
        
        # Get current container size
        w = self.frame_img.winfo_width()
        h = self.frame_img.winfo_height()
        
        # Fallback if window not mapped yet or too small
        if w < 50: w = 800
        if h < 50: h = 600
        
        # Adjust for padding/borders approx
        w = max(100, w - 20) 
        h = max(100, h - 40)
        
        try:
            # Calculate aspect ratio
            img_w, img_h = self.raw_image.size
            ratio = min(w / img_w, h / img_h)
            
            new_w = int(img_w * ratio)
            new_h = int(img_h * ratio)
            
            # Resize
            if new_w > 0 and new_h > 0:
                resized = self.raw_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
                self.current_img = ImageTk.PhotoImage(resized)
                self.lbl_img.configure(image=self.current_img, text="")
        except Exception as e:
            print(f"Display Image Error: {e}")

    def append_log(self, text):
        self.txt_log.config(state="normal")
        self.txt_log.insert("end", text + "\n")
        self.txt_log.see("end")
        self.txt_log.config(state="disabled")

    def clear(self):
        self.txt_log.config(state="normal")
        self.txt_log.delete("1.0", "end")
        self.txt_log.config(state="disabled")
        self.lbl_img.configure(image="", text="Waiting...")
