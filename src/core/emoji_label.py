import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import sys
from .platform_utils import IS_LINUX

try:
    from pilmoji import Pilmoji
except ImportError:
    Pilmoji = None

def render_emoji_image(text, font_spec=("DejaVu Sans", 12), fg="white", master=None):
    """Utility to render text with emojis to an ImageTk.PhotoImage."""
    if not Pilmoji or not IS_LINUX:
        return None
        
    try:
        from .platform_utils import get_base_dir
        family = font_spec[0]
        size = font_spec[1]
        
        # Standardize color
        if not isinstance(fg, tuple):
            if master:
                try:
                    rgb = master.winfo_rgb(fg)
                    fg = (rgb[0] >> 8, rgb[1] >> 8, rgb[2] >> 8)
                except: fg = (255, 255, 255)
            else:
                fg = (255, 255, 255)

        base_dir = get_base_dir()
        fallbacks = [
            os.path.join(base_dir, "assets", "AdorNoirrit.ttf"),
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        ]
        
        pil_font = None
        for p in fallbacks:
            if os.path.exists(p):
                try:
                    pil_font = ImageFont.truetype(p, size)
                    break
                except: continue
        
        if not pil_font: pil_font = ImageFont.load_default()
        
        w = int(pil_font.getlength(text)) + 30 # More padding
        h = int(size * 1.8) + 10 # More height for comfort
        
        img = Image.new("RGBA", (w, h), (0,0,0,0))
        with Pilmoji(img) as pilmoji:
            pilmoji.text((10, 5), text, font=pil_font, fill=fg)

        
        bbox = img.getbbox()
        if bbox: img = img.crop(bbox)
        
        return ImageTk.PhotoImage(img, master=master)
    except Exception as e:
        import logging
        from . import platform_utils
        logging.error(f"render_emoji_image error for '{text}': {e}")
        return None


class EmojiLabel(ttk.Label):
    """
    A label that renders emojis and Bengali correctly on Linux using images.
    On other platforms, it behaves like a normal ttk.Label.
    """
    def __init__(self, master, text="", font=None, **kwargs):
        self._image_ref = None 
        super().__init__(master, **kwargs)
        if text:
            self.set_text(text, font)

    def set_text(self, text, font=None):
        if not IS_LINUX or not Pilmoji:
            self.config(text=text)
            if font: self.config(font=font)
            return

        # On Linux, render entirely to image
        try:
            from .platform_utils import get_base_dir
            
            # Extract size/color
            size = 16
            if font and isinstance(font, tuple) and len(font) > 1:
                size = font[1]
                
            fg_tk = self.cget("foreground")
            def get_rgb(color_tk):
                if not color_tk or str(color_tk).startswith("System"): return (255, 255, 255)
                try:
                    rgb = self.winfo_rgb(color_tk)
                    return (rgb[0] >> 8, rgb[1] >> 8, rgb[2] >> 8)
                except: return (255, 255, 255)
            fg = get_rgb(fg_tk)

            # Load Bengali Font
            font_path = os.path.join(get_base_dir(), "assets", "AdorNoirrit.ttf")
            if not os.path.exists(font_path):
                font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            
            try:
                pil_font = ImageFont.truetype(font_path, size)
            except:
                pil_font = ImageFont.load_default()

            # Measure and Draw
            # We use a large enough temporary image for measurement
            dummy_img = Image.new("RGBA", (1, 1), (0,0,0,0))
            draw = ImageDraw.Draw(dummy_img)
            
            # Use raqm if available (for Bengali ligatures)
            w = int(pil_font.getlength(text)) + 20
            h = int(size * 1.5) + 10
            
            img = Image.new("RGBA", (w, h), (0,0,0,0))
            
            # Check if text has emojis
            has_emoji = any(ord(c) > 0x2000 for c in text)
            
            if has_emoji:
                with Pilmoji(img) as pilmoji:
                    # Y offset for emojis to align with text
                    pilmoji.text((5, 5), text, font=pil_font, fill=fg)
            else:
                # Direct Pillow rendering for best quality/ligatures
                draw = ImageDraw.Draw(img)
                draw.text((5, 5), text, font=pil_font, fill=fg)

            # Crop and set
            bbox = img.getbbox()
            if bbox: img = img.crop(bbox)
            
            self._image_ref = ImageTk.PhotoImage(img)
            self.config(image=self._image_ref, text="")
        except Exception as e:
            import logging
            logging.error(f"EmojiLabel error: {e}")
            from . import platform_utils
            self.config(text=platform_utils.sanitize_for_linux(text), image="")




