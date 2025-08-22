#!/bin/bash

# OBS Calibrator - macOS Build Script
# This script builds a standalone .app bundle and optionally a .dmg installer

set -e  # Exit on any error

APP_NAME="OBS_Calibrator"
DMG_NAME="OBS_Calibrator_Installer"
VERSION="1.0.0"

echo "==============================================="
echo "OBS Calibrator - macOS Build Script"
echo "==============================================="
echo

# Check if virtual environment exists
echo "[1/7] Checking virtual environment..."
if [ ! -f "venv/bin/activate" ]; then
    echo "ERROR: Virtual environment not found at 'venv/'"
    echo "Please run the installation script first:"
    echo "  ./install_macos.sh"
    exit 1
fi
echo "Virtual environment found"

# Check if main files exist
echo "[2/7] Checking source files..."
if [ ! -f "OBS_Calibrator.py" ]; then
    echo "ERROR: OBS_Calibrator.py not found"
    echo "Make sure you're in the correct directory"
    exit 1
fi

if [ ! -f "OBS_Calibrator.spec" ]; then
    echo "ERROR: OBS_Calibrator.spec not found"
    echo "PyInstaller spec file is missing"
    exit 1
fi
echo "Source files found"

# Activate virtual environment
echo "[3/7] Activating virtual environment..."
source venv/bin/activate

# Check PyInstaller installation
echo "[4/7] Checking PyInstaller installation..."
python -c "import PyInstaller; print('PyInstaller version:', PyInstaller.__version__)" 2>/dev/null || {
    echo "ERROR: PyInstaller not found in virtual environment"
    echo "Installing PyInstaller..."
    pip install pyinstaller
}

# Clean previous builds
echo "[5/7] Cleaning previous builds..."
if [ -d "build" ]; then
    echo "Removing old build directory..."
    rm -rf build
fi
if [ -d "dist" ]; then
    echo "Removing old dist directory..."
    rm -rf dist
fi

# Build with PyInstaller
echo "[6/7] Building application bundle with PyInstaller..."
echo "This may take several minutes..."
echo

pyinstaller --clean OBS_Calibrator.spec

BUILD_EXIT_CODE=$?

# Check build result
if [ $BUILD_EXIT_CODE -ne 0 ]; then
    echo
    echo "==============================================="
    echo "BUILD FAILED!"
    echo "==============================================="
    echo
    echo "PyInstaller exited with error code: $BUILD_EXIT_CODE"
    echo "Check the output above for detailed error information"
    echo
    echo "Common issues:"
    echo "- Missing dependencies: Check requirements.txt"
    echo "- QML files not found: Verify file paths in spec file"
    echo "- Import errors: Check hidden imports in spec file"
    echo "- Permission issues: Check file permissions"
    echo
    deactivate
    exit 1
fi

# Verify build output
if [ ! -d "dist/$APP_NAME.app" ]; then
    echo
    echo "ERROR: App bundle not created"
    echo "Check PyInstaller output for errors"
    deactivate
    exit 1
fi

if [ ! -f "dist/$APP_NAME.app/Contents/MacOS/$APP_NAME" ]; then
    echo
    echo "ERROR: Executable not created in app bundle"
    echo "Check PyInstaller output for errors"
    deactivate
    exit 1
fi

echo
echo "==============================================="
echo "BUILD SUCCESSFUL!"
echo "==============================================="
echo
echo "Built app bundle: dist/$APP_NAME.app"

# Get app bundle size
APP_SIZE=$(du -sh "dist/$APP_NAME.app" | cut -f1)
echo "App bundle size: $APP_SIZE"
echo

# Test the app bundle
echo "Testing app bundle..."
if [ -x "dist/$APP_NAME.app/Contents/MacOS/$APP_NAME" ]; then
    echo "✓ App bundle executable is valid"
else
    echo "✗ WARNING: App bundle executable may not be valid"
fi

echo
echo "[7/7] Creating DMG installer (optional)..."

# Check if dmgbuild is available for creating DMG
python -c "import dmgbuild" 2>/dev/null && HAS_DMGBUILD=1 || HAS_DMGBUILD=0

if [ $HAS_DMGBUILD -eq 1 ]; then
    echo "Creating DMG installer with dmgbuild..."
    
    # Create a simple dmgbuild configuration
    cat > dmg_config.py << EOF
# DMG configuration for OBS Calibrator

import os.path

# Basic settings
format = 'UDZO'
size = '200M'
files = ['dist/$APP_NAME.app']
symlinks = {'Applications': '/Applications'}

# Window settings
window_rect = ((100, 100), (600, 400))
icon_locations = {
    '$APP_NAME.app': (150, 200),
    'Applications': (450, 200),
}

# Background and appearance
background = None  # You can add a background image path here
show_status_bar = False
show_tab_view = False
show_toolbar = False
show_pathbar = False
show_sidebar = False
sidebar_width = 180

# Icon settings
icon_size = 100
text_size = 16
EOF

    python -m dmgbuild -s dmg_config.py "$DMG_NAME" "dist/$DMG_NAME.dmg"
    
    if [ $? -eq 0 ] && [ -f "dist/$DMG_NAME.dmg" ]; then
        DMG_SIZE=$(du -sh "dist/$DMG_NAME.dmg" | cut -f1)
        echo "✓ DMG created: dist/$DMG_NAME.dmg ($DMG_SIZE)"
        
        # Clean up config file
        rm -f dmg_config.py
    else
        echo "✗ DMG creation failed"
    fi
    
else
    echo "dmgbuild not available, creating simple DMG with hdiutil..."
    
    # Create temporary directory for DMG contents
    DMG_TEMP_DIR="dmg_temp"
    mkdir -p "$DMG_TEMP_DIR"
    
    # Copy app bundle to temp directory
    cp -R "dist/$APP_NAME.app" "$DMG_TEMP_DIR/"
    
    # Create Applications symlink
    ln -s /Applications "$DMG_TEMP_DIR/Applications"
    
    # Create DMG
    hdiutil create -srcfolder "$DMG_TEMP_DIR" -volname "$APP_NAME" -format UDZO "dist/$DMG_NAME.dmg"
    
    if [ $? -eq 0 ] && [ -f "dist/$DMG_NAME.dmg" ]; then
        DMG_SIZE=$(du -sh "dist/$DMG_NAME.dmg" | cut -f1)
        echo "✓ DMG created: dist/$DMG_NAME.dmg ($DMG_SIZE)"
    else
        echo "✗ DMG creation failed"
    fi
    
    # Clean up temp directory
    rm -rf "$DMG_TEMP_DIR"
fi

echo
echo "To test the build:"
echo "  open dist/$APP_NAME.app"
echo
echo "To distribute:"
if [ -f "dist/$DMG_NAME.dmg" ]; then
    echo "  1. Distribute the DMG file: dist/$DMG_NAME.dmg"
    echo "  2. Or copy the app bundle: dist/$APP_NAME.app"
else
    echo "  1. Copy the app bundle: dist/$APP_NAME.app"
    echo "  2. Users can drag it to their Applications folder"
fi
echo
echo "The standalone app includes all dependencies"
echo "and will run on macOS systems without Python installed."
echo

# Code signing reminder
echo "NOTE: For distribution outside the App Store, you may want to:"
echo "  1. Code sign the app: codesign --deep --force --sign 'Developer ID' dist/$APP_NAME.app"
echo "  2. Notarize with Apple: xcrun altool --notarize-app ..."
echo "  3. Staple the notarization: xcrun stapler staple dist/$APP_NAME.app"
echo

deactivate

echo "Build completed successfully!"
