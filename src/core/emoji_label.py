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
            os.path.join(base_dir, "src", "assets", "AdorNoirrit.ttf"),
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
        # Use Noto Color Emoji if available
        emoji_fpath = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
        with Pilmoji(img) as pilmoji:
            pilmoji.text((10, 8), text, font=pil_font, fill=fg, 
                         emoji_font_res=emoji_fpath if os.path.exists(emoji_fpath) else None)

        
        bbox = img.getbbox()
        if bbox:
            # Add a bit of padding to the bbox to prevent clipping
            img = img.crop((bbox[0]-5, bbox[1]-5, bbox[2]+5, bbox[3]+5))


        
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
        self._last_font = font
        super().__init__(master, **kwargs)
        if text:
            self.set_text(text, font)

    def configure(self, cnf=None, **kwargs):
        if cnf: kwargs.update(cnf)
        
        # Intercept text on Linux for both Image rendering OR Sanitization
        if IS_LINUX:
            if "text" in kwargs:
                text = kwargs.pop("text")
                font = kwargs.get("font") or self._last_font
                self.set_text(text, font)
                
        # For non-Linux, or if text was popping above, continue
        # Note: set_text calls super().config(), so we might duplicate config calls if we don't return here?
        # Actually set_text handles the configuration of text/image.
        # But we still need to pass other kwargs (bg, fg) to super.
        
        return super().configure(**kwargs)

    def config(self, cnf=None, **kwargs):
        return self.configure(cnf, **kwargs)

    def set_text(self, text, font=None):
        self._last_font = font
        if not text:
            super().config(text="", image="")
            return

        if not IS_LINUX or not Pilmoji:
            try:
                from . import platform_utils
                text = platform_utils.sanitize_for_linux(text)
            except: pass
            super().config(text=text)
            if font: super().config(font=font)
            return

        # On Linux, render entirely to image
        # import logging
        # logging.info(f"DEBUG_RENDER: '{text}'")
        try:
            from .platform_utils import get_base_dir
            
            # Extract size/weight from font tuple if provided
            size = 16 # Default size
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
            font_path = os.path.join(get_base_dir(), "src", "assets", "AdorNoirrit.ttf")
            if not os.path.exists(font_path):
                # Fallback to system font if custom font is missing
                font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            
            try:
                pil_font = ImageFont.truetype(font_path, size)
            except:
                pil_font = ImageFont.load_default()

            # Measure and Draw
            dummy_img = Image.new("RGBA", (1, 1), (0,0,0,0))
            draw = ImageDraw.Draw(dummy_img)
            
            # We use a large enough image then crop
            w = int(pil_font.getlength(text)) + 50
            h = int(size * 2) + 20
            
            img = Image.new("RGBA", (w, h), (0,0,0,0))
            
            # Check if text has emojis
            has_emoji = any(ord(c) > 0x2000 for c in text)
            
            if has_emoji:
                # Use Noto Color Emoji if available
                emoji_fpath = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
                with Pilmoji(img) as pilmoji:
                    # Y offset for emojis to align with text
                    pilmoji.text((5, 10), text, font=pil_font, fill=fg,
                                 emoji_font_res=emoji_fpath if os.path.exists(emoji_fpath) else None)
            else:
                draw = ImageDraw.Draw(img)
                draw.text((5, 10), text, font=pil_font, fill=fg)


            # Crop and set
            bbox = img.getbbox()
            if bbox:
                # Add a bit of padding to prevent clipping
                img = img.crop((bbox[0]-5, bbox[1]-5, bbox[2]+5, bbox[3]+5))
            
            self._image_ref = ImageTk.PhotoImage(img)
            super().config(image=self._image_ref, text="")

        except Exception as e:
            import logging
            logging.error(f"EmojiLabel error: {e}")
            from . import platform_utils
            safe_text = platform_utils.sanitize_for_linux(text)
            super().config(text=safe_text)
