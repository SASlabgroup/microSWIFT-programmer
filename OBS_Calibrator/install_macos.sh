#!/bin/bash

# OBS Calibrator - macOS/Linux Installation Script
# This script creates a virtual environment and installs all dependencies

set -e  # Exit on any error

echo "==============================================="
echo "OBS Calibrator - macOS/Linux Installation"
echo "==============================================="
echo

# Check if Python 3 is installed
echo "[1/5] Checking Python installation..."
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python is not installed or not in PATH"
    echo "Please install Python 3.13 or higher:"
    echo "  macOS: brew install python@3.13"
    echo "  Or download from: https://python.org/downloads/"
    echo
    exit 1
fi

# Check Python version
echo "[1/5] Verifying Python version..."
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
echo "Found Python version: $PYTHON_VERSION"

# Check if version is 3.13 or higher (basic check)
MAJOR_VERSION=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR_VERSION=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$MAJOR_VERSION" -lt 3 ] || ([ "$MAJOR_VERSION" -eq 3 ] && [ "$MINOR_VERSION" -lt 13 ]); then
    echo "WARNING: Python 3.13 or higher is recommended"
    echo "Current version: $PYTHON_VERSION"
    echo -n "Continue anyway? (y/N): "
    read CONTINUE
    if [ "$CONTINUE" != "y" ] && [ "$CONTINUE" != "Y" ]; then
        echo "Installation cancelled"
        exit 1
    fi
fi

echo "[2/5] Removing existing virtual environment (if any)..."
if [ -d "venv" ]; then
    rm -rf venv
    echo "Removed existing virtual environment"
fi

echo "[3/5] Creating new virtual environment..."
$PYTHON_CMD -m venv venv
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment"
    echo "Make sure you have venv module available"
    echo "Try: pip3 install virtualenv"
    echo
    exit 1
fi
echo "Virtual environment created successfully"

echo "[4/5] Activating virtual environment and upgrading pip..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    echo
    exit 1
fi

echo "Upgrading pip..."
python -m pip install --upgrade pip
if [ $? -ne 0 ]; then
    echo "WARNING: Failed to upgrade pip, continuing with existing version"
fi

echo "[5/5] Installing dependencies from requirements.txt..."
if [ ! -f "requirements.txt" ]; then
    echo "ERROR: requirements.txt not found"
    echo "Make sure you're running this script from the OBS_Calibrator directory"
    echo
    deactivate
    exit 1
fi

pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    echo "Check your internet connection and try again"
    echo
    deactivate
    exit 1
fi

echo
echo "==============================================="
echo "Installation completed successfully!"
echo "==============================================="
echo
echo "Virtual environment created at: venv/"
echo "All dependencies installed from requirements.txt"
echo
echo "To launch OBS Calibrator, run:"
echo "  ./run_obs_calibrator_macos.sh"
echo
echo "To manually activate the environment:"
echo "  source venv/bin/activate"
echo "  python OBS_Calibrator.py"
echo

deactivate

echo "Installation complete! You can now run the application."
