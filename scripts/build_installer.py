import subprocess
import sys
import os
from pathlib import Path

def build_installer():
    """Build Windows installer"""
    print("Starting installer build...")

    # Check if application is built
    app_path = Path("dist/main.dist/GetFileHash.exe")
    if not app_path.exists():
        print("Error: Application not found, please run 'python scripts/build.py' first")
        return False

    # Find Inno Setup compiler
    inno_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
    ]

    inno_path = None
    for path in inno_paths:
        if Path(path).exists():
            inno_path = path
            break

    if not inno_path:
        print("Error: Inno Setup compiler not found")
        print("Please download and install Inno Setup from https://jrsoftware.org/isdl.php")
        return False

    # Create installer output directory
    installer_dir = Path("installer")
    installer_dir.mkdir(exist_ok=True)

    print(f"Using Inno Setup compiler: {inno_path}")

    # Run Inno Setup
    cmd = [inno_path, "scripts/installer.iss"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("Installer built successfully!")
        print(f"Output directory: {installer_dir.absolute()}")

        # Show generated files
        for file in installer_dir.glob("*.exe"):
            print(f"Generated file: {file}")

        return True
    else:
        print(f"Installer build failed: {result.stderr}")
        return False

if __name__ == "__main__":
    success = build_installer()
    sys.exit(0 if success else 1)