#!/bin/bash
# Download pre-built Ghostscript for Linux (Snap package)
# Working directory: src/ghostscript/linux

set -e

WORKDIR="/mnt/d/Python/BiplobOCR/src/ghostscript/linux"
cd "$WORKDIR"

# Clean up previous attempts
rm -rf ghostscript-* install bin lib share *.tgz 2>/dev/null || true

# Download the pre-built Linux snap binary from GitHub releases
echo "=== Downloading Ghostscript 10.04.0 Snap package for Linux ==="
wget "https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs10040/gs_10.04.0_amd64_snap.tgz" -O gs-snap.tgz

echo ""
echo "=== Extracting ==="
tar -xzf gs-snap.tgz

echo ""
echo "=== Contents ==="
ls -la

echo ""
echo "=== Looking for gs binary ==="
find . -name "gs" -type f 2>/dev/null || find . -name "gs*" -type f 2>/dev/null | head -10

# Cleanup
rm -f gs-snap.tgz

echo ""
echo "=== Done ==="
