#!/bin/bash
# OBS Calibrator - Build Cleanup Script
# Removes unnecessary files after building the installer

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo "=============================================="
echo "    OBS Calibrator - Build Cleanup"
echo "=============================================="
echo ""

# Get the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT" || exit 1

# Check if we're in the right directory
if [ ! -f "src/OBS_Calibrator.py" ]; then
    echo -e "${RED}[ERROR]${NC} src/OBS_Calibrator.py not found!"
    echo "Project structure error. Expected to find src/OBS_Calibrator.py"
    exit 1
fi

# Calculate space used before cleanup
print_status "Calculating space usage before cleanup..."
BEFORE_SIZE=$(du -sh . 2>/dev/null | cut -f1)
echo "Current directory size: $BEFORE_SIZE"
echo ""

# Ask for confirmation
echo "This script will remove the following items:"
echo "  1. Virtual environment (venv/)"
echo "  2. Build artifacts (build/)"
echo "  3. Python cache (__pycache__/)"
echo "  4. Unpacked distribution files (dist/OBS_Calibrator/)"
echo ""
echo "It will KEEP:"
echo "  ✓ Your source code files"
echo "  ✓ The final .app package (if on macOS)"
echo "  ✓ Configuration and documentation files"
echo ""

read -p "Do you want to proceed with cleanup? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Cleanup cancelled"
    exit 0
fi

echo ""

# Remove virtual environment
if [ -d "venv" ]; then
    print_status "Removing virtual environment..."
    rm -rf venv
    print_success "Virtual environment removed"
else
    print_warning "Virtual environment not found"
fi

# Remove build directory
if [ -d "build" ]; then
    print_status "Removing build artifacts..."
    rm -rf build
    print_success "Build artifacts removed"
else
    print_warning "Build directory not found"
fi

# Remove all Python cache directories
print_status "Removing Python cache directories..."
PYCACHE_COUNT=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l)
if [ "$PYCACHE_COUNT" -gt 0 ]; then
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    print_success "Removed $PYCACHE_COUNT Python cache directories"
else
    print_warning "No Python cache directories found"
fi

# Remove unpacked distribution (but keep .app for macOS)
if [ -d "dist/OBS_Calibrator" ] && [ ! -f "dist/OBS_Calibrator.exe" ]; then
    print_status "Removing unpacked distribution files..."
    rm -rf "dist/OBS_Calibrator"
    print_success "Unpacked distribution removed"
fi

# Remove .DS_Store files (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    print_status "Removing .DS_Store files..."
    find . -name ".DS_Store" -type f -delete 2>/dev/null || true
    print_success ".DS_Store files removed"
fi

# Remove any .pyc files
print_status "Removing compiled Python files..."
find . -name "*.pyc" -type f -delete 2>/dev/null || true
find . -name "*.pyo" -type f -delete 2>/dev/null || true
print_success "Compiled Python files removed"

echo ""
print_status "Calculating space usage after cleanup..."
AFTER_SIZE=$(du -sh . 2>/dev/null | cut -f1)
echo "Current directory size: $AFTER_SIZE"

echo ""
echo "=============================================="
print_success "Cleanup completed successfully!"
echo "=============================================="
echo ""
echo "Space before cleanup: $BEFORE_SIZE"
echo "Space after cleanup:  $AFTER_SIZE"
echo ""
echo "To rebuild the application, run:"
echo "  ./build_installer.sh"
echo ""
