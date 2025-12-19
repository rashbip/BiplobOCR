# BiplobOCR Installer Build Script
# This script helps build the Windows installer

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  BiplobOCR Installer Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Inno Setup is installed
$innoSetupPaths = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)

$isccPath = $null
foreach ($path in $innoSetupPaths) {
    if (Test-Path $path) {
        $isccPath = $path
        break
    }
}

if (-not $isccPath) {
    Write-Host "ERROR: Inno Setup not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Inno Setup 6 from:" -ForegroundColor Yellow
    Write-Host "https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
    Write-Host ""
    $download = Read-Host "Open download page? (Y/N)"
    if ($download -eq "Y" -or $download -eq "y") {
        Start-Process "https://jrsoftware.org/isdl.php"
    }
    exit 1
}

Write-Host "Found Inno Setup: $isccPath" -ForegroundColor Green
Write-Host ""

# Clean previous builds
Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "installer\output") {
    Remove-Item "installer\output\*" -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Path "installer\output" -Force | Out-Null

# Clean temporary files
Write-Host "Cleaning temporary files..." -ForegroundColor Yellow
Get-ChildItem -Path "src" -Recurse -Filter "__pycache__" -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path "." -Recurse -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path "." -Recurse -Filter "*.pyo" | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path "." -Recurse -Filter "*.log" | Remove-Item -Force -ErrorAction SilentlyContinue

if (Test-Path "_biplob_temp") {
    Remove-Item "_biplob_temp" -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "Cleanup complete!" -ForegroundColor Green
Write-Host ""

# Verify required files exist
Write-Host "Verifying required files..." -ForegroundColor Yellow

$requiredFiles = @(
    "installer\setup.iss",
    "installer\LICENSE.txt",
    "installer\python_installer.py",
    "src\assets\icon.ico",
    "run.py",
    "requirements.txt"
)

$missing = @()
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        $missing += $file
    }
}

if ($missing.Count -gt 0) {
    Write-Host "ERROR: Missing required files:" -ForegroundColor Red
    foreach ($file in $missing) {
        Write-Host "  - $file" -ForegroundColor Red
    }
    exit 1
}

Write-Host "All required files present!" -ForegroundColor Green
Write-Host ""

# Build installer
Write-Host "Building installer..." -ForegroundColor Cyan
Write-Host ""

$buildResult = & $isccPath "installer\setup.iss"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  BUILD SUCCESSFUL!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    # Find the output file
    $outputFiles = Get-ChildItem "installer\output\*.exe"
    if ($outputFiles.Count -gt 0) {
        $outputFile = $outputFiles[0]
        $sizeInMB = [math]::Round($outputFile.Length / 1MB, 2)
        
        Write-Host "Installer created:" -ForegroundColor Green
        Write-Host "  Path: $($outputFile.FullName)" -ForegroundColor White
        Write-Host "  Size: $sizeInMB MB" -ForegroundColor White
        Write-Host ""
        
        $openFolder = Read-Host "Open output folder? (Y/N)"
        if ($openFolder -eq "Y" -or $openFolder -eq "y") {
            Start-Process "explorer.exe" -ArgumentList "/select,`"$($outputFile.FullName)`""
        }
    }
}
else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  BUILD FAILED!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Check the output above for errors." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Build process completed!" -ForegroundColor Cyan
