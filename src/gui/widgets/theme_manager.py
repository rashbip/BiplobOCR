"""
Theme Manager - Handles TTK style configuration for the application.
Extracted from app.py for better maintainability.
"""
from tkinter import ttk
from ...core.theme import THEME_COLOR, THEME_COLOR_HOVER, THEME_COLOR_ACTIVE, BG_COLOR, SURFACE_COLOR, FG_COLOR, MAIN_FONT, HEADER_FONT


def setup_custom_theme(root):
    """Configure all TTK styles for the dark theme."""
    style = ttk.Style(root)
    import sys
    if sys.platform.startswith('linux'):
        style.theme_use("default")
    else:
        try:
            style.theme_use("clam")
        except:
            style.theme_use("default")


    # Global Colors
    root.option_add("*background", BG_COLOR)
    root.option_add("*foreground", FG_COLOR)
    root.option_add("*selectBackground", THEME_COLOR)
    root.option_add("*selectForeground", "white")
    root.option_add("*Entry.fieldBackground", SURFACE_COLOR)
    root.option_add("*Listbox.background", SURFACE_COLOR)

    # -- TTK Styles --
    style.configure(".", background=BG_COLOR, foreground=FG_COLOR, troughcolor=BG_COLOR, 
                    fieldbackground=SURFACE_COLOR, borderwidth=0, darkcolor=BG_COLOR, 
                    lightcolor=BG_COLOR, selectbackground=THEME_COLOR)
    
    style.configure("TFrame", background=BG_COLOR)
    style.configure("Card.TFrame", background=SURFACE_COLOR, relief="flat")
    
    style.configure("TLabel", background=BG_COLOR, foreground=FG_COLOR, font=(MAIN_FONT, 10))
    style.configure("Header.TLabel", font=(HEADER_FONT, 24, "bold"), foreground=THEME_COLOR)
    
    style.configure("TButton", background=SURFACE_COLOR, foreground=FG_COLOR, borderwidth=0, 
                    padding=6, font=(MAIN_FONT, 10))
    style.map("TButton", background=[("active", "#3e3e3e"), ("pressed", "#4e4e4e")], 
              foreground=[("active", "white")])
    
    style.configure("Accent.TButton", background=THEME_COLOR, foreground="white", 
                    font=(MAIN_FONT, 10, "bold"))
    style.map("Accent.TButton", background=[("active", THEME_COLOR_HOVER), ("pressed", THEME_COLOR_ACTIVE)])
    
    style.configure("Danger.TButton", background="#800000", foreground="white", 
                    font=(MAIN_FONT, 10, "bold"))
    style.map("Danger.TButton", background=[("active", "#5a0000")])
    
    style.configure("TEntry", fieldbackground=SURFACE_COLOR, foreground=FG_COLOR, padding=5)
    style.configure("TCombobox", fieldbackground=SURFACE_COLOR, background=SURFACE_COLOR, 
                    foreground=FG_COLOR, arrowcolor="white")
    style.map("TCombobox", fieldbackground=[("readonly", SURFACE_COLOR)], 
              selectbackground=[("readonly", THEME_COLOR)])
    
    style.configure("Treeview", background=SURFACE_COLOR, fieldbackground=SURFACE_COLOR, 
                    foreground=FG_COLOR, borderwidth=0, rowheight=30, font=(MAIN_FONT, 10))
    style.map("Treeview", background=[("selected", THEME_COLOR)], foreground=[("selected", "white")])
    style.configure("Treeview.Heading", background=BG_COLOR, foreground="gray", 
                    font=(MAIN_FONT, 9, "bold"), relief="flat")
    style.map("Treeview.Heading", background=[("active", BG_COLOR)])
    
    style.configure("TSeparator", background="#3e3e3e")
    style.configure("TCheckbutton", background=BG_COLOR, foreground=FG_COLOR)
    style.map("TCheckbutton", background=[("active", BG_COLOR)], indicatorcolor=[("selected", THEME_COLOR)])
    
    style.configure("TLabelframe", background=BG_COLOR, foreground=FG_COLOR, bordercolor="#3e3e3e")
    style.configure("TLabelframe.Label", background=BG_COLOR, foreground=THEME_COLOR)
    
    style.configure("Vertical.TScrollbar", gripcount=0, background=SURFACE_COLOR, 
                    darkcolor=BG_COLOR, lightcolor=BG_COLOR, troughcolor=BG_COLOR, 
                    bordercolor=BG_COLOR, arrowcolor="white")
    style.map("Vertical.TScrollbar", background=[("active", "#4e4e4e")])
    
    style.configure("Horizontal.TProgressbar", background=THEME_COLOR, troughcolor=SURFACE_COLOR, 
                    bordercolor=SURFACE_COLOR, lightcolor=THEME_COLOR, darkcolor=THEME_COLOR)
