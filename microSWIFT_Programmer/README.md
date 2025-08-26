# microSWIFT Programmer

A configuration and programming tool for microSWIFT drift buoys.

## 📋 Prerequisites

Before using this application, you must install the following:

### Required Software

1. **Python 3.12 or higher**
   - Download: [https://www.python.org/downloads/](https://www.python.org/downloads/)
   - ⚠️ **Important:** During installation, check "Add Python to PATH"
   - Verify installation: `python --version` or `python3 --version`

2. **STM32CubeProgrammer**
   - Download: [https://www.st.com/en/development-tools/stm32cubeprog.html](https://www.st.com/en/development-tools/stm32cubeprog.html)
   - ⚠️ **Note:** You will need to create a free ST account to download
   - Install to the default location for automatic detection:
     - **macOS:** `/Applications/STMicroelectronics/STM32Cube/STM32CubeProgrammer/`
     - **Windows:** `C:\Program Files\STMicroelectronics\STM32Cube\STM32CubeProgrammer\`
     - **Linux:** `/usr/local/STMicroelectronics/STM32Cube/STM32CubeProgrammer/`

### Hardware Requirements

- **STLink V3 programmer** for device programming
- **USB connection** to the computer
- **microSWIFT device** to program

## 🚀 Quick Start

### Option 1: Run from Source (Easiest)

#### macOS/Linux
```bash
cd microSWIFT_Programmer
./run.sh
```

#### Windows
```cmd
cd microSWIFT_Programmer
run.bat
```

The scripts automatically:
- Create a Python virtual environment
- Install all dependencies
- Launch the application

### Option 2: Build Standalone Application

#### macOS
```bash
cd microSWIFT_Programmer
./build.sh
# Application created at: dist/microSWIFT_Programmer.app
# DMG installer created at: dist/microSWIFT_Programmer.dmg
```

#### Windows
```cmd
cd microSWIFT_Programmer
build.bat
REM Application created at: dist\microSWIFT_Programmer.exe
```

## 📁 Project Structure

```
microSWIFT_Programmer/
│
├── src/                          # Source code
│   └── microSWIFT_Programmer.py  # Main application
│
├── firmware/                     # Firmware binaries
│   ├── config.bin               # Configuration binary
│   ├── microSWIFT_V2.2.elf      # Main firmware (auto-downloaded)
│   └── zeros_64k.bin            # Zero-fill binary
│
├── resources/                    # Application resources
│   ├── specs/                   # PyInstaller spec files
│   │   ├── microSWIFT_Programmer_macos.spec    # macOS spec
│   │   └── microSWIFT_Programmer_windows.spec  # Windows spec
│   ├── ui/                      # UI files
│   │   └── programmer_main_window.ui  # Main window UI
│   └── images/                  # Application images
│       └── microSWIFT_pic.png   # Application icon
│
├── scripts/                      # Build and utility scripts
│   ├── build/                   # Build scripts
│   │   ├── build_macos.sh      # macOS build script
│   │   └── build_windows.bat   # Windows build script
│   │
│   ├── run/                     # Run-from-source scripts
│   │   ├── run_from_source.sh  # macOS/Linux run script
│   │   └── run_from_source.bat # Windows run script
│   │
│   └── clean/                   # Cleanup scripts
│       ├── cleanup_macos.sh    # macOS cleanup script
│       └── cleanup_windows.bat # Windows cleanup script
│
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── TROUBLESHOOTING.md           # Troubleshooting guide
├── LICENSE                       # License file
│
└── Convenience Scripts (root)    # Quick access scripts
    ├── build.sh / build.bat     # Quick build
    └── run.sh / run.bat         # Quick run
```

## 💻 Command Line Options

### Bypass Firmware Update
To skip automatic firmware download on startup:

```bash
# Running from source
./run.sh --no_firmware_update                     # macOS/Linux
run.bat --no_firmware_update                      # Windows

# Standalone application
open dist/microSWIFT_Programmer.app --args --no_firmware_update   # macOS
dist\microSWIFT_Programmer.exe --no_firmware_update               # Windows
```

## 📝 Usage Notes

### Configuration Settings

The application allows you to configure:
- **Sensors:** CT, Temperature, Light, Turbidity
- **GNSS Settings:** Sample count, sampling rate, acquisition time
- **Iridium Settings:** Transmit time, modem type (V3D/V3F)
- **Timing:** Duty cycle duration
- **Device:** Tracking number

### Firmware Updates

On startup, the application automatically downloads the latest firmware from GitHub:
- Repository: [microSWIFT-V2-Binaries](https://github.com/SASlabgroup/microSWIFT-V2-Binaries)
- Version: V2.2

If the download fails:
1. Check your internet connection
2. Use `--no_firmware_update` flag to bypass
3. Or manually download and place in `firmware/` directory

### Configuration Files

When saving configuration files:
- **For reference:** Save with `.bin` extension
- **For over-the-air updates:** Save with `.sbd` extension
- **Filename limit:** 80 characters total (including extension)
- **Example:** `microSWIFT_100_config.sbd`

### Workflow

1. **Connect** STLink V3 programmer to your computer
2. **Launch** the application
3. **Configure** device settings as needed
4. **Verify** settings using the Verify button
5. **Program** the device or save configuration

## 🛠️ Development

### Building from Source

#### Prerequisites for Building
- Python 3.12+
- All dependencies in `requirements.txt`
- PyInstaller (included in requirements)

#### Build Process

The build scripts (`build.sh` / `build.bat`) will:
1. Create a virtual environment
2. Install all dependencies
3. Build with PyInstaller
4. Create platform-specific application
5. Generate installer (DMG on macOS, optional NSIS on Windows)

### Cleaning Build Artifacts

```bash
# macOS/Linux
./scripts/clean/cleanup_macos.sh

# Windows
scripts\clean\cleanup_windows.bat
```

This removes:
- Build and dist directories
- Python cache files
- Virtual environments
- Generated executables
- Log files

**Note:** Source files and configurations are preserved.

### Python Dependencies

All dependencies are listed in `requirements.txt`:
- `PyQt6>=6.5.0` - GUI framework
- `pyserial>=3.5` - Serial communication
- `requests>=2.28.0` - HTTP client for firmware downloads
- `pyinstaller>=6.0.0` - Application bundling
- `Pillow>=10.0.0` - Image processing for icon conversion

### Adding Resources

- **Images:** Place in `resources/images/`
- **UI files:** Place in `resources/ui/`
- **Firmware:** Place in `firmware/`

### Path Resolution

The application uses dynamic path resolution that works in both development and frozen (PyInstaller) states:
- `get_resource_path()` - Base resource path resolution
- `get_firmware_path()` - Firmware file paths
- `get_image_path()` - Image file paths
- `get_ui_path()` - UI file paths

## 🔧 Troubleshooting

### Common Issues

#### Python Not Found
- Ensure Python 3.12+ is installed
- Windows: Check "Add Python to PATH" during installation
- macOS/Linux: Python 3 should be available as `python3`

#### STM32CubeProgrammer Not Found
- Install from the link above (requires ST account)
- Install to default location for automatic detection
- Linux users: May need to add to PATH manually

#### STLink V3 Not Detected
- Check USB connection
- Install STLink drivers if on Windows
- Try different USB port
- Verify device appears in system device manager

#### Build Fails
1. Run cleanup script to remove old artifacts
2. Ensure Python version is 3.12+
3. Check all resource files exist
4. Try running from source first to identify issues

#### Application Won't Start
- Verify all prerequisites are installed
- Check firmware files are present in `firmware/`
- Run from source to see detailed error messages
- Check TROUBLESHOOTING.md for more solutions

For detailed troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## 📊 System Requirements

- **Operating System:** 
  - macOS 10.13 or later
  - Windows 10 or later
  - Linux (Ubuntu 20.04+ or equivalent)
- **Python:** 3.12 or higher
- **RAM:** 4GB minimum
- **Storage:** 500MB for application + firmware
- **Display:** 1024x768 minimum resolution

## 🎨 Features

- **Cross-platform:** Works on macOS, Windows, and Linux
- **Theme Support:** Automatically adapts to system light/dark mode
- **Auto-update:** Downloads latest firmware on startup
- **Validation:** Built-in configuration verification
- **Export:** Save configurations for later use or OTA updates

## 📄 Version Information

- **Current Version:** 1.3
- **Firmware Version:** V2.2
- **Python Requirement:** ≥3.12

## 📜 License

Please refer to the LICENSE file for usage terms and conditions.

## 🤝 Support

For issues or questions:
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review command-line options above
3. Ensure all prerequisites are installed
4. Visit the project repository for updates

## 🔗 External Resources

- [Python Downloads](https://www.python.org/downloads/)
- [STM32CubeProgrammer](https://www.st.com/en/development-tools/stm32cubeprog.html)
- [microSWIFT Firmware Repository](https://github.com/SASlabgroup/microSWIFT-V2-Binaries)
- [STLink Drivers](https://www.st.com/en/development-tools/stsw-link009.html)

---

*For the latest updates and source code, visit the project repository.*
