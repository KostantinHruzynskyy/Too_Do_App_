#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════╗
║           SKYY – Build Script for .exe            ║
║  Packages the desktop app as a Windows executable ║
╚═══════════════════════════════════════════════════╝

Usage:
    python build_exe.py
    
Output:
    dist/TooDooApp.exe
"""

import os
import sys
import subprocess


def build_executable():
    """Build the desktop application as a Windows executable."""
    
    print("=" * 60)
    print("  SKYY – Building Desktop Executable")
    print("=" * 60)
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=TooDooApp",
        "--onefile",
        "--windowed",
        "--add-data=app/static;app/static",
        "--add-data=app/templates;app/templates",
        "--hidden-import=PyQt5",
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui",
        "--hidden-import=requests",
        "--hidden-import=urllib3",
        "--hidden-import=certifi",
        "--hidden-import=charset_normalizer",
        "--hidden-import=idna",
        # Icon (optional - create one if desired)
        # "--icon=app/static/images/icon.ico",
        "desktop_app.py"
    ]
    
    print("\nRunning PyInstaller...")
    print(f"Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("  BUILD SUCCESSFUL!")
        print("=" * 60)
        print(f"\nExecutable location: dist/TooDooApp.exe")
        print("\nTo run the application:")
        print("  1. Start the web server: python run.py")
        print("  2. Run the desktop app: dist/TooDooApp.exe")
        print("\nNote: The desktop app connects to http://127.0.0.1:5000")
        print("      Make sure the web server is running first.")
    else:
        print("\n" + "=" * 60)
        print("  BUILD FAILED!")
        print("=" * 60)
        print("Check the output above for errors.")
        return False
    
    return True


def create_spec_file():
    """Create a PyInstaller spec file for advanced configuration."""
    
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['desktop_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app/static', 'app/static'),
        ('app/templates', 'app/templates'),
    ],
    hiddenimports=[
        'PyQt5',
        'PyQt5.QtWidgets',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'requests',
        'urllib3',
        'certifi',
        'charset_normalizer',
        'idna',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TooDooApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='app/static/images/icon.ico',  # Uncomment if you have an icon
)
'''
    
    with open("TooDooApp.spec", "w") as f:
        f.write(spec_content)
    
    print("Created TooDooApp.spec file")


if __name__ == "__main__":
    # Optionally create spec file first
    if "--spec" in sys.argv:
        create_spec_file()
        print("\nSpec file created. Build with:")
        print("  pyinstaller TooDooApp.spec")
    else:
        build_executable()