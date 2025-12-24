#!/bin/bash
# ==============================================================================
# BiplobOCR AppImage Build Script
# ==============================================================================
# This script bundles the BiplobOCR Linux distribution into a standalone AppImage.
# It should be run on a Linux system (Ubuntu 20.04+ recommended) or WSL.
# ==============================================================================

set -e

# --- Configuration ---
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
APP_NAME="BiplobOCR"
VERSION="1.0.0"
DIST_DIR="$PROJECT_ROOT/dist"
APPDIR="$DIST_DIR/$APP_NAME.AppDir"
OUTPUT_APPIMAGE="$DIST_DIR/BiplobOCR-x86_64.AppImage"

cd "$PROJECT_ROOT"

echo ">>> Phase 1: Building PyInstaller Bundle <<<"
if [ ! -f "$PROJECT_ROOT/platforms/linux/build_bundle.sh" ]; then
    echo "Error: platforms/linux/build_bundle.sh not found."
    exit 1
fi
chmod +x "$PROJECT_ROOT/platforms/linux/build_bundle.sh"
"$PROJECT_ROOT/platforms/linux/build_bundle.sh"

echo ">>> Phase 2: Preparing AppDir Structure <<<"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

echo ">>> Phase 3: Copying Files to AppDir <<<"
# Copy PyInstaller output (from COLLECT name 'BiplobOCR_Linux_Bundle')
if [ ! -d "$DIST_DIR/BiplobOCR_Linux_Bundle" ]; then
    echo "Error: PyInstaller bundle not found at $DIST_DIR/BiplobOCR_Linux_Bundle"
    exit 1
fi
cp -r "$DIST_DIR/BiplobOCR_Linux_Bundle/"* "$APPDIR/usr/bin/"

echo ">>> Phase 4: Creating AppRun Script <<<"
cat <<EOF > "$APPDIR/AppRun"
#!/bin/bash
# AppRun for BiplobOCR AppImage

# Determine the directory where AppRun is located
HERE="\$(cd "\$(dirname "\$0")" && pwd)"

# Add our bundled binaries to PATH and LD_LIBRARY_PATH
export PATH="\$HERE/usr/bin:\$PATH"
export LD_LIBRARY_PATH="\$HERE/usr/bin:\$LD_LIBRARY_PATH"

# Set Tcl/Tk environment variables (essential for Tkinter in bundle)
# PyInstaller copies them to the root of the bundle (now usr/bin)
export TCL_LIBRARY="\$HERE/usr/bin/tcl"
export TK_LIBRARY="\$HERE/usr/bin/tk"

# OCRmyPDF often needs these set for encoding stability
export LANG="C.UTF-8"
export LC_ALL="C.UTF-8"
export PYTHONIOENCODING="utf-8"

# Launch the application
exec "\$HERE/usr/bin/BiplobOCR" "\$@"
EOF
chmod +x "$APPDIR/AppRun"

echo ">>> Phase 5: Creating Desktop Entry & Icon <<<"
cat <<EOF > "$APPDIR/biplobocr.desktop"
[Desktop Entry]
Name=BiplobOCR
Exec=BiplobOCR
Icon=biplobocr
Type=Application
Categories=Office;OCR;Scanning;
Comment=Advanced OCR Tool with Multi-language Support
Terminal=false
StartupWMClass=BiplobOCR
EOF

# Copy icon to the standard locations
if [ -f "src/assets/icon.png" ]; then
    cp "src/assets/icon.png" "$APPDIR/biplobocr.png"
    cp "src/assets/icon.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/biplobocr.png"
else
    echo "Warning: src/assets/icon.png not found. Using a placeholder."
    # If icon is missing, we still need something for AppImage to build
    touch "$APPDIR/biplobocr.png"
fi

# Link the desktop file to the root for AppImageTool
ln -sf "biplobocr.desktop" "$APPDIR/AppDir.desktop"

echo ">>> Phase 6: Downloading/Checking appimagetool <<<"
# Download appimagetool if not valid
# Note: x86_64 architecture assumed for the build environment
if [ ! -s "appimagetool" ] || ! file appimagetool | grep -q 'ELF'; then
    echo "Downloading appimagetool-x86_64.AppImage..."
    rm -f appimagetool
    wget -O appimagetool https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x appimagetool
fi

echo ">>> Phase 7: Generating Final AppImage <<<"
export ARCH=x86_64
./appimagetool --appimage-extract-and-run "$APPDIR" "$OUTPUT_APPIMAGE"

echo "=============================================================================="
echo " SUCCESS: AppImage created at $OUTPUT_APPIMAGE"
echo " You can now run the standalone linux app: "
echo " chmod +x $OUTPUT_APPIMAGE"
echo " ./$(basename "$OUTPUT_APPIMAGE")"
echo "=============================================================================="
