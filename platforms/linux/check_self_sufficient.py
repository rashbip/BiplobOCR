#!/usr/bin/env python3
import os
import sys
import shutil

def check_dependencies():
    """Verifies that all required bundled dependencies are present."""
    # Current dir: platforms/linux/
    # Project root: ../../
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    src_dir = os.path.join(project_root, "src")
    
    dependencies = [
        # Tesseract
        {"name": "Tesseract Binary", "path": os.path.join(src_dir, "tesseract", "linux", "tesseract")},
        {"name": "Tessdata", "path": os.path.join(src_dir, "tesseract", "linux", "tessdata")},
        
        # Ghostscript
        {"name": "Ghostscript Binary", "path": os.path.join(src_dir, "ghostscript", "linux", "bin", "gs")},
        
        # Assets
        {"name": "App Icon (PNG)", "path": os.path.join(src_dir, "assets", "icon.png")},
        {"name": "Custom Font", "path": os.path.join(src_dir, "assets", "AdorNoirrit.ttf")},
    ]

    missing = []
    print("Checking dependencies...")
    for dep in dependencies:
        if os.path.exists(dep["path"]):
            print(f"  [OK] {dep['name']}")
        else:
            print(f"  [MISSING] {dep['name']} at {dep['path']}")
            missing.append(dep["name"])

    # Check for Zenity (to bundle)
    zenity_path = shutil.which("zenity")
    if zenity_path:
         print(f"  [OK] Zenity found at {zenity_path} (Will be bundled)")
    else:
         print("  [WARNING] Zenity not found on host system! Cannot bundle.")
         missing.append("Zenity (System)")

    if missing:
        print("\nCRITICAL: Missing dependencies! Cannot build self-sufficient AppImage.")
        sys.exit(1)
    
    print("\nAll dependencies verified.")

if __name__ == "__main__":
    check_dependencies()
