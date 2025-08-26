# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# Get the spec file directory and project root
spec_dir = os.path.dirname(os.path.abspath(SPEC))
project_root = os.path.abspath(os.path.join(spec_dir, '..', '..'))

# Simple hidden imports based on actual application imports
hidden_imports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui', 
    'PyQt6.QtWidgets',
    'serial',
    'serial.tools',
    'serial.tools.list_ports',
    'requests'
]

a = Analysis(
    [os.path.join(project_root, 'src', 'microSWIFT_Programmer.py')],
    pathex=[project_root],
    binaries=[],
    datas=[
        (os.path.join(project_root, 'resources'), 'resources'),
        (os.path.join(project_root, 'firmware'), 'firmware')
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unused Qt modules to reduce size and avoid conflicts
        'PyQt6.Qt3D*', 'PyQt6.QtWebEngine*', 'PyQt6.QtWebView*',
        'PyQt6.QtDataVisualization', 'PyQt6.QtCharts', 'PyQt6.QtQuick*',
        'PyQt6.QtQml*', 'PyQt6.QtMultimedia*', 'PyQt6.QtBluetooth',
        'PyQt6.QtNfc', 'PyQt6.QtPositioning', 'PyQt6.QtSensors'
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='microSWIFT_Programmer',
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
    icon=os.path.join(project_root, 'resources', 'images', 'microSWIFT_pic.png'),
)
