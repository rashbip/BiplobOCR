#!/bin/bash
# Create a portable Linux distribution of BiplobOCR
# This uses the working venv and bundles everything into one folder.

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

OUT_DIR="dist/BiplobOCR_Portable_Linux"
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

echo "=== Creating Portable Linux Folder ==="

# 1. Copy Source and Assets
cp -r src "$OUT_DIR/"
cp run.py "$OUT_DIR/"
# Note: assets are already in src/assets

# 2. Add Launcher
cat <<EOF > "$OUT_DIR/BiplobOCR"
#!/bin/bash
# BiplobOCR Portable Launcher
HERE="\$(cd "\$(dirname "\$0")" && pwd)"
cd "\$HERE"

# Setup Tcl/Tk paths (if they exist in our bundle, which they should if we manage to bundle them)
# For now, we rely on the venv and system tk.

# Activate venv
source "\$HERE/src/python/linux/venv/bin/activate"

# Run
python3 run.py "\$@"
EOF

chmod +x "$OUT_DIR/BiplobOCR"

echo "=== Done! ==="
echo "Portable app is at: $OUT_DIR"
echo "Run it with: ./dist/BiplobOCR_Portable_Linux/BiplobOCR"
