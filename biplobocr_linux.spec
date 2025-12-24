# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

# Project root
base_dir = os.path.abspath(os.getcwd())

added_files = [
    ('src/assets', 'src/assets'),
    ('src/tesseract/linux', 'src/tesseract/linux'),
    ('src/ghostscript/linux', 'src/ghostscript/linux'),
    # Tcl/Tk libraries (essential for Linux file dialogs in bundle)
    ('/usr/share/tcltk/tcl8.6', 'tcl'),
    ('/usr/share/tcltk/tk8.6', 'tk'),
    # Only include the specific python source folders needed, EXCLUDING the venv
    ('src/core', 'src/core'),
    ('src/gui', 'src/gui'),
    ('src/__init__.py', 'src'),
    ('src/main.py', 'src'),
]

a = Analysis(
    ['run.py'],
    pathex=[base_dir],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'tkinterdnd2',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL._tkinter_resanitize',
        'ocrmypdf',
        'pikepdf',
        'fitz',
        'lxml',
        'reportlab',
        'reportlab.graphics.barcode',
        'reportlab.graphics.barcode.common',
        'reportlab.graphics.barcode.code128',
        'reportlab.graphics.barcode.code39',
        'reportlab.graphics.barcode.usps',
        'reportlab.graphics.barcode.qr',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['platforms/windows', 'src/python/windows', 'src/tesseract/windows', 'src/ghostscript/windows'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BiplobOCR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True, 
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BiplobOCR_Linux_Bundle',
)
