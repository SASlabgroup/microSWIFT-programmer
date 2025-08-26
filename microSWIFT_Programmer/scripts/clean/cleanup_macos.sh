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

# Remove PyInstaller build directory
if [ -d "build" ]; then
    echo "Removing build directory..."
    rm -rf build
fi

# Remove PyInstaller intermediate build artifacts from dist directory
# (Keep the .app and .dmg files but remove the onedir distribution)
if [ -d "dist/microSWIFT_Programmer" ]; then
    echo "Removing PyInstaller onedir build artifact from dist/..."
    rm -rf "dist/microSWIFT_Programmer"
fi

# Note: Preserving dist directory with final built applications
echo -e "${YELLOW}Note: Preserving dist/ directory with built applications${NC}"

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

# Note: Preserving app bundles in root directory (these shouldn't exist here anyway)
# The actual built apps are in dist/ which we're preserving

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
echo "  • Build directory"
echo "  • Python cache and compiled files"
echo "  • Virtual environments"
echo "  • Launcher scripts"
echo "  • Log files"
echo "  • macOS .DS_Store files"
echo ""
echo "The following items have been preserved:"
echo "  • dist/ directory with built applications (.app and .dmg)"
echo "  • Source files and configurations"
echo "  • Firmware files"
echo ""
echo -e "${YELLOW}To remove built applications, manually delete the dist/ directory${NC}"
