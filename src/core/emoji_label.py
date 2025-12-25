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
    A label that renders emojis correctly on Linux using pilmoji.
    On other platforms, it behaves like a normal ttk.Label.
    """
    def __init__(self, master, text="", font=None, **kwargs):
        self._orig_text = text
        self._orig_font = font
        self._image_ref = None # Prevent GC
        
        super().__init__(master, **kwargs)
        
        if text:
            self.set_text(text, font)

    def set_text(self, text, font=None):
        self._orig_text = text
        if font:
            self._orig_font = font
            
        if not IS_LINUX or not Pilmoji:
            self.config(text=text)
            if font:
                self.config(font=font)
            return

        # On Linux, render to image
        self._render_emoji_text(text, self._orig_font)

    def _render_emoji_text(self, text, font_spec):
        # Extract font details
        family = "DejaVu Sans"
        size = 14

        style = "normal"
        
        if isinstance(font_spec, tuple):
            family = font_spec[0]
            if len(font_spec) > 1: size = font_spec[1]
            if len(font_spec) > 2: style = font_spec[2]
        
        # Determine foreground color (Pillow needs valid color name or hex)
        fg_tk = self.cget("foreground")
        
        def standardize_color(color_tk):
            if not color_tk or str(color_tk).startswith("System"):
                return (255, 255, 255) # Default white
            try:
                # Use winfo_rgb to get (r, g, b) from Tkinter
                rgb = self.winfo_rgb(color_tk)
                # Tkinter returns 16-bit values (0-65535), convert to 8-bit
                return (rgb[0] >> 8, rgb[1] >> 8, rgb[2] >> 8)
            except:
                return (255, 255, 255)

        fg = standardize_color(fg_tk)
        
        # Create a dummy image to get text size
        try:
            # We need a real ttf file for pilmoji to work well on Linux
            from .platform_utils import get_base_dir
            font_path = os.path.join(get_base_dir(), "assets", "AdorNoirrit.ttf")
            
            # Fallback font paths for Linux
            fallbacks = [
                font_path,
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
            ]
            
            pil_font = None
            for p in fallbacks:
                if os.path.exists(p):
                    try:
                        pil_font = ImageFont.truetype(p, size)
                        break
                    except: continue
            
            if not pil_font:
                # Last resort: load default PIL font (wont support emojis well but wont crash)
                pil_font = ImageFont.load_default()
            
            # Measure text
            w = int(pil_font.getlength(text)) + 30
            h = int(size * 1.8) + 10
            
            img = Image.new("RGBA", (w, h), (0,0,0,0))
            with Pilmoji(img) as pilmoji:
                pilmoji.text((10, 5), text, font=pil_font, fill=fg)

            
            # Trim image to content
            bbox = img.getbbox()
            if bbox:
                img = img.crop(bbox)
            
            self._image_ref = ImageTk.PhotoImage(img)
            self.config(image=self._image_ref, text="")
        except Exception as e:
            from . import platform_utils
            logging.error(f"EmojiLabel error: {e}")
            # Safety: Sanitize text for Linux to avoid X11 crash
            self.config(text=platform_utils.sanitize_for_linux(text), image="")


