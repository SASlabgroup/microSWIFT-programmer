# OBS Calibrator

A professional PySide6-based application for calibrating Optical Backscatter (OBS) sensors used in water quality monitoring. This application supports both hardware and simulation modes for development and field deployment.

## Features

- **Multi-point calibration** (up to 10 calibration points)
- **Real-time sensor data collection** with statistical analysis
- **Linear regression modeling** with R² calculation
- **Hardware integration** with VCNL4010 proximity sensors via I2C
- **Automatic simulation mode** when hardware is not available
- **Data export** to CSV format
- **Calibration plot generation** and export
- **Cross-platform support** (Windows, macOS, Linux)
- **Dark theme interface** for professional use

## System Requirements

### Required Software
- **Python 3.13 or higher** (required for all platforms)
- **Git** (for cloning the repository)

### Supported Platforms
- **Windows 10/11** (x86-64)
- **macOS** (Intel and Apple Silicon)
- **Linux** (x86-64) - basic support

### Hardware (Optional)
- **VCNL4010 proximity sensor** via I2C
- **MCP2221 USB-to-I2C bridge** for computer connectivity
- Application runs in simulation mode when hardware is not connected

## Quick Start

### 1. Install Python 3.13+

**Windows:**
- Download from [python.org](https://www.python.org/downloads/)
- During installation, check "Add Python to PATH"
- Verify installation: `python --version`

**macOS:**
- Install via Homebrew: `brew install python@3.13`
- Or download from [python.org](https://www.python.org/downloads/)
- Verify installation: `python3 --version`

### 2. Clone the Repository

```bash
git clone <repository-url>
cd OBS_Calibrator
```

### 3. Run Installation Script

**Windows:**
```cmd
install_windows.bat
```

**macOS/Linux:**
```bash
chmod +x install_macos.sh
./install_macos.sh
```

### 4. Launch the Application

**Windows:**
```cmd
run_obs_calibrator_windows.bat
```

**macOS/Linux:**
```bash
chmod +x run_obs_calibrator_macos.sh
./run_obs_calibrator_macos.sh
```

## Manual Installation

If you prefer to install manually or encounter issues with the automated scripts:

### 1. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Application
```bash
python OBS_Calibrator.py
```

## Building Installers (Advanced)

For creating standalone executable installers:

### Prerequisites
- Complete the installation steps above
- PyInstaller (included in requirements.txt)

### Build Commands

**Windows (.exe):**
```cmd
build_windows.bat
```

**macOS (.app and .dmg):**
```bash
chmod +x build_macos.sh
./build_macos.sh
```

Built installers will be available in the `dist/` directory.

## Usage

### Hardware Mode
1. Connect VCNL4010 sensor via MCP2221 USB bridge
2. Launch application - it will automatically detect hardware
3. Set up calibration points with known NTU concentrations
4. Collect sensor readings for each calibration point
5. Generate calibration curve and export results

### Simulation Mode
1. Launch application without hardware connected
2. Application automatically enters simulation mode
3. Mock sensor data is generated for testing and demonstration
4. All calibration features work identically to hardware mode

### Key Features
- **Calibration Points**: Configure 1-10 calibration points
- **Sample Collection**: Collect multiple samples per point with automatic statistics
- **Quality Control**: Standard deviation monitoring with visual indicators
- **Data Export**: Save raw data and calibration curves
- **Professional UI**: Dark theme optimized for field use

## Troubleshooting

### Common Issues

**"No module named..." errors:**
- Ensure virtual environment is activated
- Re-run installation script
- Check Python version: `python --version`

**Hardware not detected:**
- Verify USB connection and MCP2221 drivers
- Check device permissions (Linux/macOS)
- Application will run in simulation mode if hardware unavailable

**Application won't start:**
- Check console output for error messages
- Ensure all dependencies are installed
- Try running directly: `python OBS_Calibrator.py`

**Dark theme not working:**
- Theme is enforced at application level
- Check console for Qt-related warnings
- Try running with different Qt styles

### Getting Help

1. Check console output for error messages
2. Verify all installation steps were completed
3. Ensure Python 3.13+ is installed and accessible
4. Try running in simulation mode first

## Development

### Project Structure
```
OBS_Calibrator/
├── OBS_Calibrator.py          # Main application file
├── Sensor_Thread.py           # Hardware interface and simulation
├── requirements.txt           # Python dependencies
├── qtquickcontrols2.conf     # Qt theme configuration
├── OBS_Calibration_WindowContent/  # QML user interface files
├── Python/autogen/           # Auto-generated settings
└── scripts/                  # Installation and build scripts
```

### Dependencies
- **PySide6**: Qt-based GUI framework
- **matplotlib**: Plotting and visualization
- **numpy**: Numerical computing
- **scikit-learn**: Linear regression modeling
- **Adafruit libraries**: Hardware communication (optional)
- **PyInstaller**: Executable building

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]

---

**Note**: This application is designed for scientific and industrial use. Always verify calibration results against known standards before field deployment.
