# microSWIFT-programmer

A configuration and programming tool for microSWIFT devices.

## Prerequisites

### Required Software
1. **Python 3.12 or higher** - [Download Python](https://www.python.org/downloads/)
2. **STM32CubeProgrammer** - [Download from ST](https://www.st.com/en/development-tools/stm32cubeprog.html) (Account required)
   - The CLI version is used by this application
   - Install to default location for automatic detection

## Quick Start

### Option 1: Build Standalone Application (Recommended)

#### macOS
```bash
cd microSWIFT_Programmer
./build_macos.sh
# Application will be created at: dist/microSWIFT_Programmer.app
```

#### Windows
```cmd
cd microSWIFT_Programmer
build_windows.bat
REM Application will be created at: dist\microSWIFT_Programmer.exe
```

### Option 2: Run from Source

#### macOS/Linux
```bash
cd microSWIFT_Programmer
./run_from_source.sh
```

#### Windows
```cmd
cd microSWIFT_Programmer
run_from_source.bat
```

The run scripts automatically:
- Create a virtual environment
- Install all dependencies
- Launch the application

### Option 3: Manual Installation

1) Clone or download this repository
2) Navigate to the microSWIFT_Programmer directory
3) Install dependencies:
```bash
python3 -m pip install --upgrade pip
python3 -m pip install PyQt6 pyserial requests
```
4) Run the program:
```bash
python3 src/microSWIFT_Programmer.py
```

## Command Line Options

### Bypass Firmware Update
To skip automatic firmware download on startup:
```bash
# Standalone app on macOS
open dist/microSWIFT_Programmer.app --args --no_firmware_update

# Standalone app on Windows
dist\microSWIFT_Programmer.exe --no_firmware_update

# Running from source
python3 src/microSWIFT_Programmer.py --no_firmware_update
```

## Usage Notes

### Version Information
The application version is displayed in the window title bar. Ensure you're using the latest version from this repository.

### Firmware Updates
On startup, the application automatically downloads the latest firmware (`microSWIFT_V2.2.elf`) from GitHub. If the download fails:
1. Check your internet connection
2. Manually download from [microSWIFT binaries repo](https://github.com/SASlabgroup/microSWIFT-V2-Binaries/tree/main/V2.2)
3. Place the file in the `firmware/` directory

### Configuration Files
When saving configuration files:
- For reference: Save with `.bin` extension
- For over-the-air updates: Save with `.sbd` extension
- Keep filename under 80 characters total (including extension)
- Example: `microSWIFT_100_config.sbd`

## Project Structure

```
microSWIFT_Programmer/
├── src/                          # Source code
│   └── microSWIFT_Programmer.py  # Main application
├── firmware/                     # Firmware files
│   ├── config.bin               # Configuration template
│   └── zeros_64k.bin            # Initialization file
├── resources/                    # Application resources
│   ├── images/                  # Image assets
│   └── ui/                      # UI files
├── build_macos.sh               # macOS build script
├── build_windows.bat            # Windows build script
├── cleanup_macos.sh             # macOS cleanup script
├── cleanup_windows.bat          # Windows cleanup script
├── run_from_source.sh           # macOS/Linux source runner
├── run_from_source.bat          # Windows source runner
├── requirements.txt             # Python dependencies
├── BUILD_INSTRUCTIONS.md        # Detailed build guide
└── TROUBLESHOOTING.md           # Problem-solving guide
```

## Troubleshooting

For common issues and solutions, see [TROUBLESHOOTING.md](microSWIFT_Programmer/TROUBLESHOOTING.md)

## Development

### Cleaning Build Artifacts

```bash
# macOS
cd microSWIFT_Programmer
./cleanup_macos.sh

# Windows
cd microSWIFT_Programmer
cleanup_windows.bat
```

### Building for Distribution

See [BUILD_INSTRUCTIONS.md](microSWIFT_Programmer/BUILD_INSTRUCTIONS.md) for detailed build instructions.

## System Requirements

- **Operating System:** macOS 10.13+, Windows 10+, or Linux
- **Python:** 3.12 or higher
- **RAM:** 4GB minimum
- **Storage:** 500MB for application + firmware
- **Hardware:** STLink V3 programmer for device programming

## License

Please refer to the repository license file for usage terms.

