#!/bin/bash
# OBS Calibrator - Automated Installer (macOS/Linux)
# This script sets up the development environment and builds a standalone application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get Python version
get_python_version() {
    if command_exists python3; then
        python3 --version 2>&1 | cut -d' ' -f2
    elif command_exists python; then
        python --version 2>&1 | cut -d' ' -f2
    else
        echo "0.0.0"
    fi
}

# Function to check if version meets minimum requirement
version_ge() {
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

echo "=============================================="
echo "    OBS Calibrator - Automated Installer"
echo "=============================================="
echo ""

# Check for Python 3.12+
print_status "Checking Python installation..."

PYTHON_VERSION=$(get_python_version)
if [ "$PYTHON_VERSION" = "0.0.0" ]; then
    print_error "Python is not installed or not in PATH!"
    echo ""
    echo "Please install Python 3.12 or higher:"
    echo "  macOS: brew install python@3.13"
    echo "  Linux: sudo apt install python3.13 python3.13-venv"
    echo ""
    exit 1
fi

if ! version_ge "$PYTHON_VERSION" "3.12.0"; then
    print_error "Python $PYTHON_VERSION detected. Python 3.12+ is required!"
    echo ""
    echo "Please upgrade Python:"
    echo "  macOS: brew install python@3.13"
    echo "  Linux: sudo apt install python3.13 python3.13-venv"
    echo ""
    exit 1
fi

print_success "Python $PYTHON_VERSION detected"

# Determine which Python command to use
if command_exists python3; then
    PYTHON_CMD="python3"
elif command_exists python; then
    PYTHON_CMD="python"
else
    print_error "No Python command found!"
    exit 1
fi

print_status "Using Python command: $PYTHON_CMD"

# Check if we're in the right directory
if [ ! -f "OBS_Calibrator.py" ]; then
    print_error "OBS_Calibrator.py not found!"
    echo "Please run this script from the OBS_Calibrator directory."
    exit 1
fi

# Create virtual environment
print_status "Creating virtual environment..."
if [ -d "venv" ]; then
    print_warning "Virtual environment already exists. Removing..."
    rm -rf venv
fi

$PYTHON_CMD -m venv venv
if [ $? -ne 0 ]; then
    print_error "Failed to create virtual environment!"
    echo "Please ensure python3-venv is installed:"
    echo "  Ubuntu/Debian: sudo apt install python3-venv"
    echo "  macOS: Should be included with Python"
    exit 1
fi

print_success "Virtual environment created"

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
print_status "Installing Python dependencies..."
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found!"
    exit 1
fi

pip install -r requirements.txt
if [ $? -ne 0 ]; then
    print_error "Failed to install dependencies!"
    echo "Please check the requirements.txt file and try again."
    exit 1
fi

print_success "Dependencies installed successfully"

# Build application with PyInstaller
print_status "Building standalone application..."
if [ ! -f "OBS_Calibrator.spec" ]; then
    print_error "OBS_Calibrator.spec not found!"
    exit 1
fi

pyinstaller --noconfirm OBS_Calibrator.spec
if [ $? -ne 0 ]; then
    print_error "Failed to build application!"
    echo "Check the console output above for details."
    exit 1
fi

print_success "Application built successfully"

# Check what was built
if [ -d "dist/OBS_Calibrator.app" ]; then
    APP_PATH="dist/OBS_Calibrator.app"
    print_success "macOS Application built: $APP_PATH"
    echo ""
    echo "To run the application:"
    echo "  1. Open Finder and navigate to the project directory"
    echo "  2. Go to the 'dist' folder"
    echo "  3. Double-click 'OBS_Calibrator.app'"
    echo ""
    echo "Or from terminal:"
    echo "  open \"$APP_PATH\""
    
elif [ -f "dist/OBS_Calibrator/OBS_Calibrator" ]; then
    APP_PATH="dist/OBS_Calibrator/OBS_Calibrator"
    print_success "Linux Application built: dist/OBS_Calibrator/"
    echo ""
    echo "To run the application:"
    echo "  cd dist/OBS_Calibrator"
    echo "  ./OBS_Calibrator"
    echo ""
    echo "Or from current directory:"
    echo "  \"$APP_PATH\""
else
    print_warning "Application built but location unclear. Check the dist/ directory."
fi

# Deactivate virtual environment
deactivate

echo ""
echo "=============================================="
print_success "Installation completed successfully!"
echo "=============================================="
echo ""
echo "What happens next:"
echo "  1. The standalone application is ready to use"
echo "  2. No Python environment needed to run the app"
echo "  3. The app will work on similar systems without installation"
echo ""
echo "If you need to run from source instead, use:"
echo "  ./run_from_source.sh"
echo ""
