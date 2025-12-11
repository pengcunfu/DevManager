import os
import sys

# 配置
VERSION = "0.0.1"
YEAR = "2025"
AUTHOR = "GetFileHash"

if sys.platform == "win32":
    args = [
        'nuitka',
        '--standalone',
        '--windows-console-mode=disable',
        '--plugin-enable=pyside6',
        '--assume-yes-for-downloads',
        '--msvc=latest',
        '--windows-icon-from-ico=resources/icon.png',
        '--company-name=GetFileHash',
        '--product-name="GetFileHash SHA-256 Calculator"',
        f'--file-version={VERSION}',
        f'--product-version={VERSION}',
        '--file-description="GetFileHash SHA-256 Calculator"',
        f'--copyright="Copyright(C) {YEAR} {AUTHOR}"',
        '--output-dir=dist',
        '--output-filename=GetFileHash.exe',
        'main.py',
    ]

    if "--onefile" in sys.argv:
        args.pop(args.index("--standalone"))
        args.insert(1, "--onefile")

elif sys.platform == "darwin":
    args = [
        'python3 -m nuitka',
        '--standalone',
        '--plugin-enable=pyside6',
        '--static-libpython=no',
        '--macos-create-app-bundle',
        '--assume-yes-for-downloads',
        '--macos-app-mode=gui',
        f'--macos-app-version={VERSION}',
        '--macos-app-icon=resources/icon.png',
        f'--copyright="Copyright(C) {YEAR} {AUTHOR}"',
        '--output-dir=dist',
        'main.py',
    ]
else:
    args = [
        'nuitka',
        '--standalone',
        '--plugin-enable=pyside6',
        '--include-qt-plugins=platforms',
        '--assume-yes-for-downloads',
        '--linux-icon=resources/icon.png',
        '--output-dir=dist',
        'main.py',
    ]

os.system(' '.join(args))