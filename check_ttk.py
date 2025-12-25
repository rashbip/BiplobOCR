import tkinter as tk
from tkinter import ttk
import sys

print(f"Python: {sys.version}")
root = tk.Tk()
style = ttk.Style(root)
style.theme_use("clam")

print("Testing ttk.PanedWindow...")
pw = ttk.PanedWindow(root, orient="horizontal")
pw.pack(fill="both", expand=True)

f1 = ttk.Frame(pw, width=200, height=200)
pw.add(f1)

print("Testing styled ttk.Label...")
style.configure("Test.TLabel", font=("DejaVu Sans", 24, "bold"))
lbl = ttk.Label(f1, text="Test Label", style="Test.TLabel")
lbl.pack()

print("Updating...")
root.update()
print("Success!")
root.destroy()
