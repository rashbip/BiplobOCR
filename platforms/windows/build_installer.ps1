# BiplobOCR Simple Build Script
# This script bundles the app into a single installer using Inno Setup.

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  BiplobOCR Simple Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Verification
$isccPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $isccPath)) {
    $isccPath = "C:\Program Files\Inno Setup 6\ISCC.exe"
}

if (-not (Test-Path $isccPath)) {
    Write-Host "ERROR: Inno Setup 6 not found. Please install it." -ForegroundColor Red
    exit 1
}

# 2. Cleanup Noise
Write-Host "Pruning cache and temporary files..." -ForegroundColor Yellow
$rootDir = Resolve-Path "..\.."

# Remove Python/Tesseract cache and temp files
Get-ChildItem -Path "$rootDir" -Recurse -Include "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Get-ChildItem -Path "$rootDir" -Recurse -Include "*.pyc", "*.pyo", "*.log" -ErrorAction SilentlyContinue | Remove-Item -Force
if (Test-Path "$rootDir\_biplob_temp") { Remove-Item "$rootDir\_biplob_temp" -Recurse -Force }
if (Test-Path "$rootDir\config.json") { Remove-Item "$rootDir\config.json" -Force }
if (Test-Path "$rootDir\history.json") { Remove-Item "$rootDir\history.json" -Force }

# 3. Build Explorer
Write-Host "Building Installer (LZMA2 Maximum Compression)..." -ForegroundColor Cyan
& $isccPath "installer\setup.iss"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nSUCCESS! Installer created in platforms\windows\installer\output\" -ForegroundColor Green
    $output = Get-ChildItem "installer\output\*.exe" | Select-Object -First 1
    Write-Host "Size: $([math]::Round($output.Length / 1MB, 2)) MB" -ForegroundColor White
}
else {
    Write-Host "`nBUILD FAILED!" -ForegroundColor Red
}
