#!/bin/bash
# OBS Calibrator - Source Runner (macOS/Linux)
# This script runs the application from source with proper virtual environment handling

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

echo "=============================================="
echo "      OBS Calibrator - Running from Source"
echo "=============================================="
echo ""

# Get the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT" || exit 1

# Check if we're in the right directory
if [ ! -f "src/OBS_Calibrator.py" ]; then
    print_error "src/OBS_Calibrator.py not found!"
    echo "Project structure error. Expected to find src/OBS_Calibrator.py"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found!"
    echo ""
    echo "Please run the dependency installer first:"
    echo "  ./install_dependencies.sh"
    echo ""
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    local exit_code=$?
    print_status "Cleaning up..."
    
    # Deactivate virtual environment if it's active
    if [ -n "$VIRTUAL_ENV" ]; then
        print_status "Deactivating virtual environment..."
        deactivate 2>/dev/null || true
    fi
    
    if [ $exit_code -eq 0 ]; then
        print_success "Application exited normally"
    else
        print_warning "Application exited with code $exit_code"
    fi
    
    exit $exit_code
}

# Set up trap to ensure cleanup happens
trap cleanup EXIT INT TERM

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    print_error "Failed to activate virtual environment!"
    echo "Try reinstalling dependencies:"
    echo "  ./install_dependencies.sh"
    exit 1
fi

print_success "Virtual environment activated"

# Check if required packages are installed
print_status "Checking dependencies..."
python -c "import PySide6, matplotlib, numpy, sklearn" 2>/dev/null
if [ $? -ne 0 ]; then
    print_error "Required dependencies are missing!"
    echo ""
    echo "Please reinstall dependencies:"
    echo "  ./install_dependencies.sh"
    echo ""
    exit 1
fi

print_success "Dependencies verified"

# Run the application
print_status "Starting OBS Calibrator..."
echo ""

# Run the Python application from src directory - let it handle its own output
python src/OBS_Calibrator.py

# Note: The cleanup function will be called automatically when the script exits
# This ensures the virtual environment is properly deactivated regardless of how the app exits
