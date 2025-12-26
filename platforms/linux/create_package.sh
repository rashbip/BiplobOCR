#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
DIST_ARCHIVE="$SCRIPT_DIR/BiplobOCR-Linux-Installer.tar.gz"

echo "Creating Linux Release Package..."

# 1. Ensure AppImage exists
APPIMAGE="$SCRIPT_DIR/BiplobOCR-x86_64.AppImage"
if [ ! -f "$APPIMAGE" ]; then
    echo "Error: AppImage not found at $APPIMAGE"
    echo "Please run appimage_builder.sh first!"
    exit 1
fi

# 2. Gather files into a temp directory
STAGING_DIR="$SCRIPT_DIR/staging"
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"

echo "Staging files..."
cp "$APPIMAGE" "$STAGING_DIR/"
cp "$SCRIPT_DIR/install.sh" "$STAGING_DIR/"
cp "$PROJECT_ROOT/src/assets/icon.png" "$STAGING_DIR/"

chmod +x "$STAGING_DIR/install.sh"
chmod +x "$STAGING_DIR/BiplobOCR-x86_64.AppImage"

# 3. Create Archive (Tarball)
echo "Compressing..."
cd "$SCRIPT_DIR"
tar -czvf "$DIST_ARCHIVE" -C "$STAGING_DIR" .

# Cleanup
rm -rf "$STAGING_DIR"

echo "------------------------------------------------"
echo "Package Created Successfully!"
echo "Artifact: $DIST_ARCHIVE"
echo "------------------------------------------------"
echo "To distribute:"
echo "1. Share BiplobOCR-Linux-Installer.tar.gz"
echo "2. User extracts it -> runs 'sudo ./install.sh'"
