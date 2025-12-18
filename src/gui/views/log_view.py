import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import fitz

class LogView(tk.Toplevel):
    def __init__(self, parent, title="Process Details"):
        super().__init__(parent)
        self.title(title)
        self.geometry("900x600")
        
        # Split: Left (Image) | Right (Log)
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left: Image Viewer
        self.frame_img = ttk.LabelFrame(paned, text="Processing Page", padding=10)
        paned.add(self.frame_img, weight=1)
        
        self.lbl_img = ttk.Label(self.frame_img, text="Waiting for process...", anchor="center")
        self.lbl_img.pack(fill="both", expand=True)
        
        # Middle: Log/Text
        self.frame_log = ttk.LabelFrame(paned, text="Live Log", padding=10)
        paned.add(self.frame_log, weight=1)
        
        self.txt_log = tk.Text(self.frame_log, background="#1e1e1e", foreground="#d4d4d4", font=("Consolas", 10), state="disabled", wrap="word")
        self.txt_log.pack(side="left", fill="both", expand=True)
        
        scroll_log = ttk.Scrollbar(self.frame_log, command=self.txt_log.yview)
        scroll_log.pack(side="right", fill="y")
        self.txt_log.config(yscrollcommand=scroll_log.set)
        
        # Right: Extracted Text
        self.frame_text = ttk.LabelFrame(paned, text="Extracted Text (Real-time)", padding=10)
        paned.add(self.frame_text, weight=1)
        
        self.txt_text = tk.Text(self.frame_text, background="#1e1e1e", foreground="#d4d4d4", font=("Segoe UI", 10), state="disabled", wrap="word")
        self.txt_text.pack(side="left", fill="both", expand=True)
        
        # Initial placeholder
        self.append_text("Text will appear here as pages are completed...")
        
        scroll_text = ttk.Scrollbar(self.frame_text, command=self.txt_text.yview)
        scroll_text.pack(side="right", fill="y")
        self.txt_text.config(yscrollcommand=scroll_text.set)
        
        # State
        self.current_img = None

    def update_image(self, pdf_path, page_num):
        """Renders the specific page from the PDF and displays it."""
        try:
            doc = fitz.open(pdf_path)
            if page_num < 0 or page_num >= len(doc): return
            
            page = doc[page_num]
            pix = page.get_pixmap(dpi=150) # Moderate DPI for speed
            img_data = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Resize to fit frame container?
            # For now, just simplistic scale down if huge
            max_h = 500
            if img_data.height > max_h:
                ratio = max_h / img_data.height
                img_data = img_data.resize((int(img_data.width * ratio), max_h), Image.Resampling.LANCZOS)
                
            self.current_img = ImageTk.PhotoImage(img_data)
            self.lbl_img.configure(image=self.current_img, text="")
            doc.close()
        except Exception as e:
            self.append_log(f"Error rendering page preview: {e}\n")

    def append_log(self, text):
        self.txt_log.config(state="normal")
        self.txt_log.insert("end", text + "\n")
        self.txt_log.see("end")
        self.txt_log.config(state="disabled")

    def append_text(self, text):
        self.txt_text.config(state="normal")
        self.txt_text.insert("end", text + "\n\n")
        self.txt_text.see("end")
        self.txt_text.config(state="disabled")

    def clear(self):
        self.txt_log.config(state="normal")
        self.txt_log.delete("1.0", "end")
        self.txt_log.config(state="disabled")
        
        self.txt_text.config(state="normal")
        self.txt_text.delete("1.0", "end")
        self.txt_text.config(state="disabled")
        
        self.lbl_img.configure(image="", text="Waiting...")
