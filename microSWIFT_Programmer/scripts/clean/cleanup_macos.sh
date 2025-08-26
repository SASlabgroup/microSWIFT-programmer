#!/bin/bash

# microSWIFT_Programmer macOS Cleanup Script
# This script removes all build artifacts and temporary files

echo "========================================="
echo "microSWIFT_Programmer Cleanup Script"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the project root directory (two levels up from scripts/clean/)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${YELLOW}Cleaning build artifacts...${NC}"

# Remove PyInstaller build directories
if [ -d "build" ]; then
    echo "Removing build directory..."
    rm -rf build
fi

if [ -d "dist" ]; then
    echo "Removing dist directory..."
    rm -rf dist
fi

# Remove PyInstaller spec file work directories
if [ -d "__pycache__" ]; then
    echo "Removing __pycache__ directory..."
    rm -rf __pycache__
fi

# Remove compiled Python files
echo "Removing compiled Python files..."
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Remove virtual environment
if [ -d ".venv" ]; then
    echo "Removing virtual environment..."
    rm -rf .venv
fi

if [ -d "venv" ]; then
    echo "Removing venv directory..."
    rm -rf venv
fi

# Remove generated app bundles
if [ -d "microSWIFT_Programmer.app" ]; then
    echo "Removing microSWIFT_Programmer.app..."
    rm -rf microSWIFT_Programmer.app
fi

if [ -d "microSWIFT_Programmer_Source.app" ]; then
    echo "Removing microSWIFT_Programmer_Source.app..."
    rm -rf microSWIFT_Programmer_Source.app
fi

# Remove launcher scripts
if [ -f "run_microSWIFT_Programmer.command" ]; then
    echo "Removing run_microSWIFT_Programmer.command..."
    rm -f run_microSWIFT_Programmer.command
fi

# Remove log files
echo "Removing log files..."
find . -type f -name "*.log" -delete

# Remove .DS_Store files (macOS specific)
echo "Removing .DS_Store files..."
find . -type f -name ".DS_Store" -delete

# Remove PyInstaller work files
if [ -f "*.spec.bak" ]; then
    echo "Removing spec backup files..."
    rm -f *.spec.bak
fi

# Optional: Remove downloaded firmware (uncomment if desired)
# if [ -f "firmware/microSWIFT_V2.2.elf" ]; then
#     echo "Removing downloaded firmware..."
#     rm -f firmware/microSWIFT_V2.2.elf
# fi

echo -e "${GREEN}✓ Cleanup completed!${NC}"
echo ""
echo "The following items have been removed:"
echo "  • Build and dist directories"
echo "  • Python cache and compiled files"
echo "  • Virtual environments"
echo "  • Generated app bundles"
echo "  • Launcher scripts"
echo "  • Log files"
echo "  • macOS .DS_Store files"
echo ""
echo "Source files and configurations have been preserved."
