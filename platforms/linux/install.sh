#!/bin/bash
set -e

# Configuration
INSTALL_DIR="/opt/BiplobOCR"
BIN_DIR="/usr/local/bin"
DESKTOP_DIR="/usr/share/applications"
ICON_DIR="/usr/share/icons/hicolor/256x256/apps"

APPNAME="BiplobOCR"
APPIMAGE_NAME="BiplobOCR-x86_64.AppImage"

# Ensure root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root (sudo ./install.sh)"
  exit 1
fi

echo "Installing $APPNAME..."

# 1. Install AppImage to /opt
echo "[1/4] Moving Application Files..."
mkdir -p "$INSTALL_DIR"
cp "$APPIMAGE_NAME" "$INSTALL_DIR/$APPIMAGE_NAME"
chmod +x "$INSTALL_DIR/$APPIMAGE_NAME"

# Copy Icon if present
if [ -f "icon.png" ]; then
    cp "icon.png" "$INSTALL_DIR/icon.png"
    # Try global icon path
    if [ -d "$ICON_DIR" ]; then
        cp "icon.png" "$ICON_DIR/$APPNAME.png"
    fi
fi

# Copy Uninstaller to Opt
if [ -f "uninstall.sh" ]; then
    cp "uninstall.sh" "$INSTALL_DIR/uninstall.sh"
    chmod +x "$INSTALL_DIR/uninstall.sh"
fi

# 2. Create Symlink
echo "[2/4] Creating Command Alias..."
ln -sf "$INSTALL_DIR/$APPIMAGE_NAME" "$BIN_DIR/biplobocr"

# 3. Create Desktop Entry
echo "[3/4] Creating Desktop Entry..."
cat > "$DESKTOP_DIR/$APPNAME.desktop" <<EOF
[Desktop Entry]
Name=$APPNAME
Exec=$INSTALL_DIR/$APPIMAGE_NAME --no-sandbox %F
Icon=$APPNAME
Type=Application
Categories=Office;Utility;
Comment=Advanced PDF OCR Solution
Terminal=false
StartupWMClass=BiplobOCR
MimeType=application/pdf;
EOF

chmod 644 "$DESKTOP_DIR/$APPNAME.desktop"

# 4. Updates for User Data if strictly needed?
# Usually not needed as the app handles ~/.local/share creation on first run.

echo "[4/4] Updating Icon Cache..."
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache /usr/share/icons/hicolor || true
fi

echo "-----------------------------------"
echo "Installation Complete!"
echo "Run from terminal: biplobocr"
echo "Or find 'BiplobOCR' in your application menu."
echo ""
echo "To uninstall: sudo /opt/BiplobOCR/uninstall.sh"
echo "-----------------------------------"
