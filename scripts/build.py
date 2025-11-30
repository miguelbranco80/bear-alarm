#!/usr/bin/env python3
"""
Cross-platform build script for Bear Alarm.

This script packages Bear Alarm as a standalone application using Flet's
built-in packaging (which uses PyInstaller under the hood).

Usage:
    python scripts/build.py [--platform macos|windows|linux]
    
The packaged app will be in the dist/ directory.
"""

import argparse
import os
import platform
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


def get_platform() -> str:
    """Get current platform name."""
    system = platform.system()
    if system == "Darwin":
        return "macos"
    elif system == "Windows":
        return "windows"
    else:
        return "linux"


def check_dependencies():
    """Verify required tools are installed."""
    print("📋 Checking dependencies...")
    
    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ required")
        sys.exit(1)
    print(f"  ✓ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check flet is installed
    try:
        import flet
        print(f"  ✓ Flet {flet.version.version}")
    except ImportError:
        print("❌ Flet not installed. Run: pip install flet")
        sys.exit(1)


def clean_build():
    """Clean previous build artifacts."""
    print("🧹 Cleaning previous builds...")
    
    dirs_to_clean = ["dist", "build", "__pycache__"]
    for dir_name in dirs_to_clean:
        path = ROOT / dir_name
        if path.exists():
            shutil.rmtree(path)
            print(f"  ✓ Removed {dir_name}/")


def copy_resources():
    """Copy resource files to build location."""
    print("📦 Preparing resources...")
    
    # Ensure resources directory exists and has files
    sounds_dir = ROOT / "resources" / "sounds"
    if not sounds_dir.exists():
        print("⚠️  No resources/sounds/ directory found")
    else:
        print(f"  ✓ Alert sounds: {list(sounds_dir.glob('*'))}")
    
    # Copy icon
    icon_src = ROOT / "resources" / "icons" / "bear-icon.png"
    if icon_src.exists():
        print(f"  ✓ Icon: {icon_src}")


def build_flet(target_platform: str):
    """Build using Flet's packaging."""
    print(f"🔨 Building for {target_platform}...")
    
    # Determine icon file based on platform
    if target_platform == "macos":
        icon = ROOT / "resources" / "icons" / "AppIcon.icns"
        if not icon.exists():
            icon = ROOT / "resources" / "icons" / "bear-icon.png"
    elif target_platform == "windows":
        icon = ROOT / "resources" / "icons" / "bear-icon.ico"
        if not icon.exists():
            icon = ROOT / "resources" / "icons" / "bear-icon.png"
    else:
        icon = ROOT / "resources" / "icons" / "bear-icon.png"
    
    # Build command
    cmd = [
        sys.executable, "-m", "flet", "pack",
        str(ROOT / "src" / "main.py"),
        "--name", APP_NAME,
        "--product-name", APP_NAME,
        "--product-version", APP_VERSION,
        "--bundle-id", BUNDLE_ID,
    ]
    
    if icon.exists():
        cmd.extend(["--icon", str(icon)])
    
    # Add resources (sounds, icons, defaults)
    resources_dir = ROOT / "resources"
    if resources_dir.exists():
        cmd.extend(["--add-data", f"{resources_dir}:resources"])
    
    print(f"  Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, cwd=ROOT)
    
    if result.returncode != 0:
        print("❌ Build failed!")
        sys.exit(1)
    
    print("✅ Build successful!")


def post_build(target_platform: str):
    """Post-build tasks."""
    dist_dir = ROOT / "dist"
    
    if target_platform == "macos":
        app_path = dist_dir / f"{APP_NAME}.app"
        if app_path.exists():
            print(f"📱 macOS app created: {app_path}")
            print("\n  To install:")
            print(f"    cp -r '{app_path}' /Applications/")
            print("\n  Or drag to Applications folder in Finder")
            
    elif target_platform == "windows":
        exe_path = dist_dir / f"{APP_NAME}.exe"
        if exe_path.exists():
            print(f"🪟 Windows executable created: {exe_path}")
            print("\n  To create installer, use Inno Setup or NSIS")
            
    elif target_platform == "linux":
        binary_path = dist_dir / APP_NAME.lower().replace(" ", "-")
        if binary_path.exists():
            print(f"🐧 Linux binary created: {binary_path}")
            print("\n  To install system-wide:")
            print(f"    sudo cp '{binary_path}' /usr/local/bin/")
            print("\n  Or create an AppImage/Flatpak for distribution")


def main():
    parser = argparse.ArgumentParser(
        description="Build Bear Alarm for distribution"
    )
    parser.add_argument(
        "--platform",
        choices=["macos", "windows", "linux"],
        default=get_platform(),
        help="Target platform (default: current platform)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build artifacts before building",
    )
    parser.add_argument(
        "--no-build",
        action="store_true",
        help="Only clean, don't build",
    )
    
    args = parser.parse_args()
    
    print(f"🐻 Bear Alarm Build Script v{APP_VERSION}")
    print("=" * 50)
    
    os.chdir(ROOT)
    
    if args.clean or args.no_build:
        clean_build()
    
    if args.no_build:
        print("✅ Clean complete")
        return
    
    check_dependencies()
    copy_resources()
    build_flet(args.platform)
    post_build(args.platform)
    
    print("\n" + "=" * 50)
    print("🎉 Build complete!")


if __name__ == "__main__":
    main()

