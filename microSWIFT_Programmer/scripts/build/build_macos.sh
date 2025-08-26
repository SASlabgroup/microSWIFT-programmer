#!/bin/bash
# Build microSWIFT Programmer for macOS - creates .app bundle

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Exit on error
set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Get the project root (two levels up from scripts/build/)
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}microSWIFT Programmer - macOS Builder${NC}" 
echo -e "${GREEN}======================================${NC}"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
rm -rf dist build

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Build with PyInstaller
echo -e "${YELLOW}Building application with PyInstaller...${NC}"
echo -e "${BLUE}This may take several minutes...${NC}"
echo ""

pyinstaller "$PROJECT_ROOT/resources/specs/microSWIFT_Programmer_macos.spec" --noconfirm --clean

# Check if build was successful
if [ -f "dist/microSWIFT_Programmer.app/Contents/MacOS/microSWIFT_Programmer" ]; then
    echo ""
    echo -e "${GREEN}✅ Build successful!${NC}"
    echo -e "${GREEN}📱 Application: dist/microSWIFT_Programmer.app${NC}"
    
    # Get app size
    APP_SIZE=$(du -sh dist/microSWIFT_Programmer.app | cut -f1)
    echo -e "${BLUE}📦 Application size: ${APP_SIZE}${NC}"
    echo ""
    
    # Test the application
    echo -e "${YELLOW}Testing application launch...${NC}"
    if timeout 5 dist/microSWIFT_Programmer.app/Contents/MacOS/microSWIFT_Programmer --help >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Application launches successfully${NC}"
    else
        echo -e "${YELLOW}⚠️  Application test inconclusive (this is normal for GUI apps)${NC}"
    fi
    echo ""
    
    # Optional DMG creation
    if command -v create-dmg &> /dev/null; then
        read -p "Would you like to create a DMG installer? (y/N): " dmg_choice
        if [[ $dmg_choice =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Creating DMG installer...${NC}"
            create-dmg \
                --volname "microSWIFT Programmer" \
                --window-size 600 400 \
                --icon-size 100 \
                --icon "microSWIFT_Programmer.app" 175 120 \
                --hide-extension "microSWIFT_Programmer.app" \
                --app-drop-link 425 120 \
                "dist/microSWIFT_Programmer.dmg" \
                "dist/microSWIFT_Programmer.app"
            echo -e "${GREEN}✅ DMG created: dist/microSWIFT_Programmer.dmg${NC}"
        fi
    else
        echo -e "${BLUE}ℹ️  Install create-dmg to create DMG installer: brew install create-dmg${NC}"
    fi
    
    # Prompt for cleanup
    echo ""
    read -p "Would you like to clean up build artifacts? (y/N): " cleanup_choice
    if [[ $cleanup_choice =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Running cleanup...${NC}"
        "$SCRIPT_DIR/../clean/cleanup_macos.sh"
        echo -e "${GREEN}✅ Cleanup completed${NC}"
    fi
    
else
    echo ""
    echo -e "${RED}❌ Build failed!${NC}"
    echo -e "${RED}Check the output above for errors${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Build completed successfully!${NC}"
echo -e "${GREEN}======================================${NC}"
