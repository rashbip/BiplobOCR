import tkinter as tk
from tkinter import font
import sys

def test_font(name):
    print(f"Testing font: {name}...", end=" ", flush=True)
    try:
        root = tk.Tk()
        root.withdraw()
        lbl = tk.Label(root, text="Hello World! English Text Only", font=(name, 12))
        lbl.pack()
        root.update()
        root.destroy()
        print("SUCCESS")
    except Exception as e:
        print(f"FAILED: {e}")

root = tk.Tk()
fonts = list(font.families())
root.destroy()

print(f"Available fonts: {len(fonts)}")
test_fonts = ["Helvetica", "DejaVu Sans", "Liberation Sans", "sans", "serif", "mono", "Li Ador Noirrit", "Segoe UI"]
for f in test_fonts:
    test_font(f)

# Test with complex text
root = tk.Tk()
try:
    print("Testing with complex theme configuration...")
    # Simulate some of the theme_manager logic
    root.option_add("*font", "Helvetica 10")
    lbl = tk.Label(root, text="📜 BiplobOCR")
    lbl.pack()
    root.update()
    print("Complex test SUCCESS")
except Exception as e:
    print(f"Complex test FAILED: {e}")
finally:
    try: root.destroy()
    except: pass
