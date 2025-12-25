import tkinter as tk
from tkinter import ttk
import sys
import os

root = tk.Tk()
# Try different fonts
fonts = ["DejaVu Sans", "Helvetica", "sans", "Liberation Sans"]

for i, f in enumerate(fonts):
    ttk.Label(root, text=f"Test {f}: বাংলা লেখা (Bengali Test)", font=(f, 16)).pack(pady=10)

print("Updating...")
root.update()
print("Rendered successfully (check for crashes)")
root.after(2000, root.destroy)
root.mainloop()
