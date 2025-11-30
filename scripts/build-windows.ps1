# Build Bear Alarm for Windows
#
# This creates a standalone .exe that can be run without Python installed.
#
# Prerequisites:
#   - Python 3.10+
#   - uv (https://astral.sh/uv)
#
# Usage:
#   .\scripts\build-windows.ps1

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

Set-Location $ProjectDir

Write-Host "🐻 Bear Alarm - Windows Build" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Check uv
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "❌ uv is required. Install with:" -ForegroundColor Red
    Write-Host "   irm https://astral.sh/uv/install.ps1 | iex"
    exit 1
}

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
uv sync

# Clean previous builds
Write-Host "🧹 Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

# Build with flet pack
Write-Host "🔨 Building application..." -ForegroundColor Yellow

$buildArgs = @(
    "run", "python", "-m", "flet", "pack",
    "src\main.py",
    "--name", "Bear Alarm",
    "--product-name", "Bear Alarm",
    "--product-version", "0.2.0",
    "--add-data", "resources;resources"
)

# Add icon if exists
if (Test-Path "resources\icons\bear-icon.png") {
    $buildArgs += "--icon"
    $buildArgs += "resources\icons\bear-icon.png"
}

uv @buildArgs

# Check if successful
if (Test-Path "dist\Bear Alarm.exe") {
    Write-Host ""
    Write-Host "✅ Build successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📱 Executable location: dist\Bear Alarm.exe" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To create an installer, consider using:"
    Write-Host "  - Inno Setup (free): https://jrsoftware.org/isinfo.php"
    Write-Host "  - NSIS: https://nsis.sourceforge.io/"
} else {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}

