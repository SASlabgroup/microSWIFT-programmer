#!/bin/bash

# OBS Calibrator - macOS/Linux Launcher Script
# This script activates the virtual environment and launches the application

echo "==============================================="
echo "OBS Calibrator - macOS/Linux Launcher"
echo "==============================================="
echo

# Check if virtual environment exists
echo "[1/3] Checking virtual environment..."
if [ ! -f "venv/bin/activate" ]; then
    echo "ERROR: Virtual environment not found at 'venv/'"
    echo "Please run the installation script first:"
    echo "  ./install_macos.sh"
    echo
    exit 1
fi
echo "Virtual environment found"

# Check if main application exists
echo "[2/3] Checking application files..."
if [ ! -f "OBS_Calibrator.py" ]; then
    echo "ERROR: OBS_Calibrator.py not found"
    echo "Make sure you're running this script from the OBS_Calibrator directory"
    echo
    exit 1
fi
echo "Application files found"

# Function to cleanup on exit
cleanup() {
    echo
    echo "==============================================="
    echo "Application closed"
    echo "==============================================="
    
    if [ $? -ne 0 ]; then
        echo
        echo "Application exited with error code: $?"
        echo "Check the output above for error details"
        echo
        echo "Common issues:"
        echo "- Missing dependencies: Re-run ./install_macos.sh"
        echo "- Hardware connection problems: Check USB connections"
        echo "- Qt/GUI issues: Try running from terminal for detailed output"
        echo "- Permission issues: Check file permissions"
        echo
    else
        echo "Application exited normally"
    fi
    
    # Deactivate virtual environment if it was activated
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        deactivate 2>/dev/null || true
        echo "Virtual environment deactivated"
    fi
    
    exit $?
}

# Set up signal handlers to ensure cleanup
trap cleanup EXIT INT TERM

# Activate virtual environment
echo "[3/3] Activating virtual environment and launching application..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    echo "Try running the installation script again:"
    echo "  ./install_macos.sh"
    echo
    exit 1
fi

echo
echo "Starting OBS Calibrator..."
echo "Close the application window or press Ctrl+C to stop"
echo "==============================================="
echo

# Launch the application with error handling
python OBS_Calibrator.py

# Exit code will be handled by cleanup function
