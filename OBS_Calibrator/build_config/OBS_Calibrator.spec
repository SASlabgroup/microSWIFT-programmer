# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# Get the project root directory (parent of build_config)
SPEC_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = SPEC_DIR.parent
APP_NAME = "OBS_Calibrator"
MAIN_SCRIPT = str(PROJECT_ROOT / "src" / "OBS_Calibrator.py")

# Platform-specific configurations
IS_WINDOWS = sys.platform.startswith('win')
IS_MACOS = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')

# Data files to include
data_files = [
    # QML files and directories
    (str(PROJECT_ROOT / 'ui' / 'OBS_Calibration_WindowContent'), 'OBS_Calibration_WindowContent'),
    (str(PROJECT_ROOT / 'ui' / 'OBS_Calibration_Window'), 'OBS_Calibration_Window'),
    (str(PROJECT_ROOT / 'Python'), 'app_python'),  # Rename to avoid conflict
    
    # Configuration files
    (str(PROJECT_ROOT / 'ui' / 'qtquickcontrols2.conf'), '.'),
    
    # Requirements file for reference
    (str(PROJECT_ROOT / 'requirements.txt'), '.'),
    
    # README for users
    (str(PROJECT_ROOT / 'README.md'), '.'),
]

# Hidden imports that PyInstaller might miss
hidden_imports = [
    # PySide6 modules
    'PySide6.QtCore',
    'PySide6.QtGui', 
    'PySide6.QtQml',
    'PySide6.QtQuick',
    'PySide6.QtQuickControls2',
    'PySide6.QtWidgets',
    
    # Scientific libraries
    'numpy',
    'matplotlib',
    'matplotlib.backends',
    'matplotlib.backends.backend_agg',
    'matplotlib.figure',
    'scikit-learn',
    'sklearn.linear_model',
    'sklearn.metrics',
    
    # Standard library modules that might be missed
    'tempfile',
    'pathlib',
    'csv',
    'shutil',
    'statistics',
    'random',
    'time',
    
    # Hardware libraries (Adafruit Blinka and MCP2221 support)
    'board',
    'adafruit_vcnl4010',
    'adafruit_circuitpython_vcnl4010',
    'adafruit_blinka',
    'adafruit_blinka.board',
    'adafruit_blinka.board.generic_linux',
    'adafruit_blinka.board.macos',
    'adafruit_blinka.board.windows',
    'adafruit_blinka.microcontroller',
    'adafruit_blinka.microcontroller.mcp2221',
    'adafruit_platformdetect',
    'adafruit_platformdetect.board',
    'adafruit_platformdetect.chip',
    'microcontroller',
    'busio',
    'digitalio',
    'analogio',
    'pulseio',
    'pwmio',
    'neopixel_write',
    'hidapi',
    'usb',
    'hid',
    'pyusb',
]

# Collect all QML files
def collect_qml_files(qml_dir):
    """Recursively collect all QML files from a directory."""
    qml_files = []
    qml_path = PROJECT_ROOT / 'ui' / qml_dir
    if qml_path.exists():
        for qml_file in qml_path.rglob('*.qml'):
            # Preserve the original path structure for QML files
            rel_path = Path(qml_dir) / qml_file.relative_to(qml_path)
            qml_files.append((str(qml_file), str(rel_path.parent)))
    return qml_files

# Add individual QML files to ensure they're found
qml_data_files = []
qml_data_files.extend(collect_qml_files('OBS_Calibration_WindowContent'))
qml_data_files.extend(collect_qml_files('OBS_Calibration_Window'))

# Combine all data files
all_data_files = data_files + qml_data_files

a = Analysis(
    [MAIN_SCRIPT],
    pathex=[str(PROJECT_ROOT / 'src'), str(PROJECT_ROOT)],
    binaries=[],
    datas=all_data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(SPEC_DIR / 'pyi_rth_blinka.py')],
    excludes=[
        # Exclude only truly unnecessary modules
        'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Filter out duplicates and unnecessary files
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Platform-specific executable configuration
if IS_WINDOWS:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,  # Set to True for debugging
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=None,  # Add icon path here if you have one
    )
    
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=APP_NAME,
    )

elif IS_MACOS:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=APP_NAME,
    )
    
    app = BUNDLE(
        coll,
        name=f'{APP_NAME}.app',
        icon=None,  # Add icon path here if you have one
        bundle_identifier='com.example.obs-calibrator',
        info_plist={
            'CFBundleDisplayName': 'OBS Calibrator',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
            'LSMinimumSystemVersion': '10.13.0',
            'NSHumanReadableCopyright': 'Copyright © 2024 Your Organization',
            'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeName': 'CSV File',
                    'CFBundleTypeExtensions': ['csv'],
                    'CFBundleTypeRole': 'Editor',
                }
            ],
        },
    )

else:  # Linux
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
