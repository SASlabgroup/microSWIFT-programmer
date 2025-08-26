#!/bin/bash

# microSWIFT_Programmer Run-from-Source Script for macOS/Linux
# This script runs the application directly from source code

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the project root directory (two levels up from scripts/run/)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}microSWIFT Programmer - Run from Source${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    echo "Please install Python 3 from https://www.python.org/downloads/"
    exit 1
fi

# Check Python version
echo -e "${YELLOW}Python version:${NC}"
python3 --version
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
    echo ""
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate

# Check if dependencies are installed by trying to import PyQt6
python -c "import PyQt6" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
    echo ""
else
    echo -e "${GREEN}✓ Dependencies already installed${NC}"
    echo ""
fi

# Check if STM32CubeProgrammer is installed (for macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    PROGRAMMER_PATH="/Applications/STMicroelectronics/STM32Cube/STM32CubeProgrammer/STM32CubeProgrammer.app"
    if [ ! -d "$PROGRAMMER_PATH" ]; then
        echo -e "${YELLOW}Warning: STM32CubeProgrammer not found at expected location${NC}"
        echo "Please install STM32CubeProgrammer from:"
        echo "https://www.st.com/en/development-tools/stm32cubeprog.html"
        echo ""
    fi
fi

# Run the application
echo -e "${GREEN}Starting microSWIFT Programmer...${NC}"
echo "========================================="
echo ""

# Pass all command line arguments to the Python script
python src/microSWIFT_Programmer.py "$@"

# Capture the exit code
EXIT_CODE=$?

# Deactivate virtual environment
deactivate 2>/dev/null || true

# Exit with the same code as the Python script
exit $EXIT_CODE
