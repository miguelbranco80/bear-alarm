#!/usr/bin/env python3
"""
macOS build script for Bear Alarm.

Packages Bear Alarm as a standalone .app using PyInstaller.

Usage:
    python scripts/build.py
    
The packaged app will be in the dist/ directory.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


# Project root
ROOT = Path(__file__).parent.parent

# Build configuration
APP_NAME = "Bear Alarm"
APP_VERSION = "0.2.0"
BUNDLE_ID = "com.bearalarm.app"


def check_dependencies():
    """Verify required tools are installed."""
    print("📋 Checking dependencies...")
    
    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ required")
        sys.exit(1)
    print(f"  ✓ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check PyInstaller
    try:
        import PyInstaller
        print(f"  ✓ PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("  Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Check PySide6
    try:
        import PySide6
        print(f"  ✓ PySide6 {PySide6.__version__}")
    except ImportError:
        print("❌ PySide6 not installed")
        sys.exit(1)


def clean_build():
    """Clean previous build artifacts."""
    print("🧹 Cleaning previous builds...")
    
    dirs_to_clean = ["dist", "build"]
    for dir_name in dirs_to_clean:
        path = ROOT / dir_name
        if path.exists():
            shutil.rmtree(path)
            print(f"  ✓ Removed {dir_name}/")
    
    # Clean spec file
    spec_file = ROOT / f"{APP_NAME}.spec"
    if spec_file.exists():
        spec_file.unlink()
        print(f"  ✓ Removed {spec_file.name}")


def build_macos():
    """Build macOS .app bundle."""
    print("🔨 Building macOS app...")
    
    # Paths
    main_script = ROOT / "src" / "main_qt.py"
    resources_dir = ROOT / "resources"
    icon_path = resources_dir / "icons" / "AppIcon.icns"
    
    if not icon_path.exists():
        icon_path = resources_dir / "icons" / "bear-icon.png"
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--windowed",  # No console window
        "--onedir",    # Directory bundle (faster startup than onefile)
        "--noconfirm", # Overwrite without asking
        
        # macOS specific
        "--osx-bundle-identifier", BUNDLE_ID,
    ]
    
    # Add icon if exists
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    
    # Add resources
    if resources_dir.exists():
        # Add sounds
        sounds_dir = resources_dir / "sounds"
        if sounds_dir.exists():
            cmd.extend(["--add-data", f"{sounds_dir}:resources/sounds"])
        
        # Add icons
        icons_dir = resources_dir / "icons"
        if icons_dir.exists():
            cmd.extend(["--add-data", f"{icons_dir}:resources/icons"])
    
    # Hidden imports for PySide6
    cmd.extend([
        "--hidden-import", "PySide6.QtCore",
        "--hidden-import", "PySide6.QtGui", 
        "--hidden-import", "PySide6.QtWidgets",
        "--hidden-import", "PySide6.QtCharts",
    ])
    
    # Main script
    cmd.append(str(main_script))
    
    print(f"  Running PyInstaller...")
    result = subprocess.run(cmd, cwd=ROOT)
    
    if result.returncode != 0:
        print("❌ Build failed!")
        sys.exit(1)
    
    print("✅ Build successful!")


def post_build():
    """Post-build tasks."""
    app_path = ROOT / "dist" / f"{APP_NAME}.app"
    
    if app_path.exists():
        print(f"\n📱 macOS app created: {app_path}")
        print("\n  To install:")
        print(f"    cp -r 'dist/{APP_NAME}.app' /Applications/")
        print("\n  Or drag to Applications folder in Finder")
        
        # Show size
        size = sum(f.stat().st_size for f in app_path.rglob('*') if f.is_file())
        print(f"\n  App size: {size / 1024 / 1024:.1f} MB")
    else:
        print("⚠️  App bundle not found in expected location")


def main():
    print(f"🐻 Bear Alarm Build Script v{APP_VERSION}")
    print("=" * 50)
    
    os.chdir(ROOT)
    
    clean_build()
    check_dependencies()
    build_macos()
    post_build()
    
    print("\n" + "=" * 50)
    print("🎉 Build complete!")


if __name__ == "__main__":
    main()
