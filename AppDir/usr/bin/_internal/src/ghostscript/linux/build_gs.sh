#!/bin/bash
# Build Ghostscript for Linux from source
# Working directory: src/ghostscript/linux

set -e

WORKDIR="/mnt/d/Python/BiplobOCR/src/ghostscript/linux"
GS_VERSION="10.04.0"
GS_TARBALL="ghostscript-${GS_VERSION}.tar.gz"
GS_URL="https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs10040/${GS_TARBALL}"

cd "$WORKDIR"

# Clean up
rm -rf ghostscript-* gs_* install *.tgz *.snap 2>/dev/null || true

echo "=== Downloading Ghostscript ${GS_VERSION} source ==="
wget "$GS_URL" -O "$GS_TARBALL"

echo ""
echo "=== Extracting ==="
tar -xzf "$GS_TARBALL"
cd "ghostscript-${GS_VERSION}"

echo ""
echo "=== Configuring ==="
# Configure for local installation - minimal build
./configure --prefix="$WORKDIR/install" \
    --disable-cups \
    --disable-gtk \
    --without-x \
    --disable-dbus

echo ""
echo "=== Building (using $(nproc) cores) ==="
make -j$(nproc)

echo ""
echo "=== Installing locally ==="
make install

echo ""
echo "=== Cleanup ==="
cd "$WORKDIR"
rm -rf "ghostscript-${GS_VERSION}"
rm -f "$GS_TARBALL"

echo ""
echo "=== Testing ==="
"$WORKDIR/install/bin/gs" --version

echo ""
echo "=== SUCCESS! ==="
ls -la "$WORKDIR/install/bin/"
du -sh "$WORKDIR/install/"
