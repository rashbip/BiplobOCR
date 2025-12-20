# BiplobOCR Installer Build Guide

## Prerequisites

### 1. Inno Setup Compiler

Download and install **Inno Setup 6** from:

- **Official Site**: https://jrsoftware.org/isdl.php
- Choose the Unicode version
- Install with default settings

### 2. Project Files

Ensure all project files are present:

- Source code in `src/` directory
- Icon file: `src/assets/icon.ico`
- Requirements: `requirements.txt`
- License: `installer/LICENSE.txt`

## Building the Installer

### Quick Build (Recommended)

Run the automated build script:

```powershell
.\build_installer.ps1
```

This script will:

1. ✓ Check for Inno Setup installation
2. ✓ Clean all temporary files and cache
3. ✓ Verify required files are present
4. ✓ Build the installer
5. ✓ Show output location and size

### Manual Build

If you prefer manual building:

1. **Clean temporary files:**

   ```powershell
   Get-ChildItem -Path "src" -Recurse -Filter "__pycache__" -Directory | Remove-Item -Recurse -Force
   ```

2. **Open Inno Setup Compiler**

3. **Open** `installer\setup.iss`

4. **Click** Build → Compile

5. **Find output** in `installer\output\`

## What the Installer Does

### Installation Flow

1. **Welcome Screen**

   - Shows app name, version, and publisher info
   - License agreement (EULA/Terms of Service)

2. **Python Environment Check**

   - Detects if Python 3.8+ is installed
   - Shows status (Found/Not Found)

3. **Installation Directory**

   - Default: `C:\Program Files\BiplobOCR`
   - User can customize

4. **Additional Tasks** (user selectable)

   - ☑ Create Start Menu shortcut (default: checked)
   - ☐ Create Desktop icon (default: unchecked)
   - ☐ Create Quick Launch shortcut (default: unchecked)

5. **Installation**

   - Copies all application files
   - Excludes: `__pycache__`, `*.pyc`, `*.log`, temp files

6. **Python Setup**

   - Runs `python_installer.py`
   - If Python not found:
     - **Auto Install**: Downloads and installs Python 3.12.7
     - **Manual**: Opens python.org download page
     - **Add to PATH**: Guides user to add Python to PATH
   - Installs all pip packages from `requirements.txt`
   - Checks package compatibility
   - Shows progress for each package

7. **Completion**
   - Option to launch BiplobOCR immediately
   - Installation complete

## Installer Features

### Smart Python Management

- ✓ Auto-detects existing Python installations
- ✓ Offers automatic Python download & install
- ✓ Verifies Python is in system PATH
- ✓ Installs pip packages automatically
- ✓ Checks for compatible package versions
- ✓ Progress indicators for all operations

### Windows Integration

- ✓ Professional Windows installer (Inno Setup)
- ✓ Start Menu shortcuts with custom icon
- ✓ Desktop shortcut (optional)
- ✓ Quick Launch shortcut (optional)
- ✓ Proper uninstaller with cleanup
- ✓ Add/Remove Programs integration

### Clean Installation

- ✓ Excludes all cache files (`__pycache__`)
- ✓ Excludes temporary files (`_biplob_temp/`)
- ✓ Excludes log files (`*.log`)
- ✓ Excludes user configs (`config.json`, `history.json`)
- ✓ Only includes essential runtime files

### Uninstallation

The uninstaller will:

- Remove all installed files
- Clean up cache and temporary directories
- Remove shortcuts
- Remove from Add/Remove Programs
- Optionally keep user data (configs, history)

## Output

After building, you'll get:

**File**: `installer/output/BiplobOCR-Setup-1.0.0.exe`

**Approximate Size**: 65-70 MB

- Application code: ~2 MB
- Tesseract OCR: ~62 MB
- Assets & installer: ~3-5 MB

## Customization

### Change Version

Edit `installer/setup.iss`:

```pascal
#define MyAppVersion "1.0.0"  // Change here
```

### Change Default Installation Path

Edit `installer/setup.iss`:

```pascal
DefaultDirName={autopf}\{#MyAppName}  // Change {autopf} or app name
```

### Modify Icon

Replace `src/assets/icon.ico` with your custom icon (256x256 recommended)

### Update License/Terms

Edit `installer/LICENSE.txt` with your terms

### Change Python Version

Edit `installer/python_installer.py`:

```python
def get_latest_python_version(self):
    return "3.12.7"  # Update version here
```

## Testing the Installer

1. **Test on Clean Windows VM** (recommended)

   - No Python installed
   - Test auto-installation flow

2. **Test with Python Already Installed**

   - Verify package installation
   - Check compatibility checks

3. **Test Uninstallation**

   - Verify complete cleanup
   - Check shortcuts removed

4. **Test Upgrades**
   - Install older version
   - Install newer version
   - Verify upgrade works

## Troubleshooting

### "Inno Setup not found"

- Install Inno Setup 6 from https://jrsoftware.org/isdl.php
- Verify installation path

### "Missing required files"

- Run from project root directory
- Check all files are present per prerequisites

### Python installation fails

- Check internet connection
- Try manual Python installation
- Verify Windows permissions

### Package installation fails

- Check pip is installed with Python
- Verify internet connection for package downloads
- Check for package name changes

## Distribution

Once built, the installer is fully self-contained:

- Share `BiplobOCR-Setup-1.0.0.exe`
- No additional files needed
- Users just run the EXE
- Internet required for Python/package downloads if not already installed

## File Structure

```
BiplobOCR/
├── src/                        # Application source
│   ├── assets/
│   │   ├── icon.ico           # App icon
│   │   └── icon.png           # Icon PNG
│   ├── core/                  # Core modules
│   ├── gui/                   # GUI modules
│   └── tesseract/             # Tesseract OCR
├── installer/
│   ├── setup.iss              # Inno Setup script
│   ├── LICENSE.txt            # Terms of Service
│   ├── python_installer.py    # Python setup helper
│   └── output/                # Build output (gitignored)
├── run.py                     # Application entry point
├── requirements.txt           # Python dependencies
├── build_installer.ps1        # Build script
└── README.md                  # This file
```

## License

See `installer/LICENSE.txt` for the complete End User License Agreement.

---

**Need Help?** Check the project repository or contact the developer.
