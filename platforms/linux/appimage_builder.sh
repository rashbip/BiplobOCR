#!/bin/bash
set -e

# Configuration
APP_NAME="BiplobOCR"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
SRC_DIR="$PROJECT_ROOT/src"
DIST_DIR="$SCRIPT_DIR/dist"
BUILD_DIR="$SCRIPT_DIR/build"
APP_DIR="$SCRIPT_DIR/AppDir"
TEMP_SRC_DIR="$SCRIPT_DIR/temp_src_linux"

echo "Project Root: $PROJECT_ROOT"

# 1. Setup Python Environment (using bundled venv)
echo "[1/7] Setting up build environment..."
PYTHON_BIN="$SRC_DIR/python/linux/venv/bin/python"

if [ ! -f "$PYTHON_BIN" ]; then
    echo "Error: Bundled Python not found at $PYTHON_BIN"
    exit 1
fi

# Ensure PyInstaller is installed
"$PYTHON_BIN" -m pip install pyinstaller pillow pikepdf pymupdf tkinterdnd2-universal

# 2. Verify Dependencies
echo "[2/7] Verifying self-sufficiency..."
"$PYTHON_BIN" "$SCRIPT_DIR/check_self_sufficient.py"

# Ensure binaries are executable
chmod +x "$SRC_DIR/tesseract/linux/tesseract"
chmod +x "$SRC_DIR/ghostscript/linux/bin/gs"

# 3. Optimize Source (Remove Windows Bloat)
echo "[3/7] optimizing source for Linux..."
rm -rf "$TEMP_SRC_DIR"
mkdir -p "$TEMP_SRC_DIR"
cp -r "$SRC_DIR/"* "$TEMP_SRC_DIR/"

# Remove Windows-specific folders
echo "Removing Windows-specific files..."
rm -rf "$TEMP_SRC_DIR/python/windows"
rm -rf "$TEMP_SRC_DIR/ghostscript/windows"
rm -rf "$TEMP_SRC_DIR/tesseract/windows"
rm -rf "$TEMP_SRC_DIR/tesseract/mac" 2>/dev/null || true

# 4. Build with PyInstaller
echo "[4/7] Building executable..."
rm -rf "$DIST_DIR" "$BUILD_DIR"

# --add-data: Use our optimized TEMP_SRC_DIR and map it to 'src' inside the bundle
"$PYTHON_BIN" -m PyInstaller --noconfirm --onedir --windowed --clean \
    --name "$APP_NAME" \
    --add-data "$TEMP_SRC_DIR:src" \
    --add-data "$PROJECT_ROOT/README.md:." \
    --icon "$SRC_DIR/assets/icon.png" \
    --collect-all "tkinterdnd2" \
    --hidden-import "PIL._tkinter_finder" \
    --distpath "$DIST_DIR" \
    --workpath "$BUILD_DIR" \
    --specpath "$SCRIPT_DIR" \
    "$PROJECT_ROOT/run.py"

# 5. Prepare AppDir Structure
echo "[5/7] Preparing AppDir..."
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR/usr/bin"
mkdir -p "$APP_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$APP_DIR/usr/share/applications"

# Copy main executable folder content to usr/bin
cp -r "$DIST_DIR/$APP_NAME/"* "$APP_DIR/usr/bin/"

# Copy Zenity (Self-Sufficient!)
ZENITY_PATH=$(command -v zenity || true)
if [ ! -f "$ZENITY_PATH" ]; then
    # Fallback to our bundled one if system one is missing
    ZENITY_PATH="$SRC_DIR/bin/linux/zenity"
fi

if [ -f "$ZENITY_PATH" ]; then
    echo "Bundling Zenity from $ZENITY_PATH..."
    cp "$ZENITY_PATH" "$APP_DIR/usr/bin/zenity"
    chmod +x "$APP_DIR/usr/bin/zenity"
else
    echo "WARNING: Zenity not found! Native dialogs might fail if not on host."
fi

# Copy Icon
cp "$SRC_DIR/assets/icon.png" "$APP_DIR/$APP_NAME.png"
cp "$SRC_DIR/assets/icon.png" "$APP_DIR/usr/share/icons/hicolor/256x256/apps/$APP_NAME.png"

# Create Desktop File
cat > "$APP_DIR/$APP_NAME.desktop" <<EOF
[Desktop Entry]
Name=BiplobOCR
Exec=BiplobOCR
Icon=$APP_NAME
Type=Application
Categories=Utility;Office;
Comment=Advanced OCR Tool
Terminal=false
EOF
cp "$APP_DIR/$APP_NAME.desktop" "$APP_DIR/usr/share/applications/"

# Create AppRun (Entry Point)
cat > "$APP_DIR/AppRun" <<EOF
#!/bin/bash
HERE="\$(dirname "\$(readlink -f "\${0}")")"
export PATH="\${HERE}/usr/bin:\${PATH}"
export LD_LIBRARY_PATH="\${HERE}/usr/lib:\${LD_LIBRARY_PATH}"
exec "\${HERE}/usr/bin/$APP_NAME" "\$@"
EOF
chmod +x "$APP_DIR/AppRun"

# 6. Get AppImageTool
echo "[6/7] Checking for AppImageTool..."
TOOL_PATH="$SCRIPT_DIR/appimagetool"
if [ ! -f "$TOOL_PATH" ]; then
    echo "Downloading AppImageTool..."
    wget -O "$TOOL_PATH" "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
fi
chmod +x "$TOOL_PATH"

# 7. Build AppImage
echo "[7/7] Generating AppImage..."
# ARCH=x86_64 "$TOOL_PATH" --appimage-extract-and-run "$APP_DIR" "$SCRIPT_DIR/${APP_NAME}-x86_64.AppImage"
# Using --appimage-extract-and-run handles issues where fuse isn't available in some environments
ARCH=x86_64 "$TOOL_PATH" "$APP_DIR" "$SCRIPT_DIR/${APP_NAME}-x86_64.AppImage"

# Cleanup
rm -rf "$TEMP_SRC_DIR"

echo "------------------------------------------------"
echo "Build Complete!"
echo "AppImage created at: $SCRIPT_DIR/${APP_NAME}-x86_64.AppImage"
echo "------------------------------------------------"
