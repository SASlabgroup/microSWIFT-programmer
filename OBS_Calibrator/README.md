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
- **Cross-platform support** (Windows, macOS)

## System Requirements

### Required Software
- **Python 3.12 or higher** (Python 3.13 recommended)
- **Git** (for cloning the repository) - optional if downloading as ZIP

### Supported Platforms
- **Windows 10/11** (x86-64)
- **macOS** (Intel and Apple Silicon)

### Hardware (Optional)
- **VCNL4010 proximity sensor** via I2C
- **MCP2221 USB-to-I2C bridge** for computer connectivity
- Application runs in simulation mode when hardware is not connected

## 🚀 Easy Installation (Recommended)

### Step 1: Install Python

**Never used Python before? No problem!**

**Windows Users:**
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download Python 3.13 (or latest version)
3. **IMPORTANT:** During installation, check the box that says "Add Python to PATH"
4. Click "Install Now"
5. Open Command Prompt (search "cmd" in Start menu) and type: `python --version`
6. You should see something like "Python 3.13.x"

**Mac Users:**
1. **Easy way:** Install Homebrew first: [brew.sh](https://brew.sh/)
2. Then run: `brew install python@3.13`
3. **Alternative:** Download from [python.org/downloads](https://www.python.org/downloads/)
4. Open Terminal and type: `python3 --version`
5. You should see something like "Python 3.13.x"

### Step 2: Get the Code

**Option A: Using Git (if you have it)**
```bash
git clone <repository-url>
cd OBS_Calibrator
```

**Option B: Download ZIP (easier)**
1. Download the project as a ZIP file
2. Extract it to a folder (like Desktop/OBS_Calibrator)
3. Open Command Prompt (Windows) or Terminal (Mac) in that folder

### Step 3: Choose Your Installation Path

## 🎯 Path 1: Build Standalone Application (Easiest)

**This creates an app that runs without Python installed**

**Windows:**
1. Double-click `build_installer.bat`
2. Wait for it to complete (may take 5-10 minutes)
3. Find your app in the `dist` folder
4. Double-click `OBS_Calibrator.exe` to run

**Mac:**
1. Open Terminal in the project folder
2. Run: `chmod +x build_installer.sh`
3. Run: `./build_installer.sh`
4. Wait for it to complete (may take 5-10 minutes)
5. Find your app in the `dist` folder
6. Double-click `OBS_Calibrator.app` to run

## 🔧 Path 2: Run from Source (If Path 1 fails)

**Step 1: Install Dependencies**

**Windows:**
1. Double-click `install_dependencies.bat`
2. Wait for installation to complete

**Mac:**
1. Run: `chmod +x install_dependencies.sh`
2. Run: `./install_dependencies.sh`
3. Wait for installation to complete

**Step 2: Run the Application**

**Windows:**
- Double-click `run_from_source.bat`

**Mac:**
- Run: `chmod +x run_from_source.sh`
- Run: `./run_from_source.sh`

## 📋 What Each Script Does

- **`build_installer.*`**: Creates a standalone application you can run anywhere
- **`install_dependencies.*`**: Sets up a safe Python environment with all required packages
- **`run_from_source.*`**: Runs the app from Python source code (automatically handles environment)

## ✅ Quick Test

After installation, the application should:
1. Open with a professional interface
2. Show "Hardware connected" or "No Device!" in the serial number field
3. Allow you to configure calibration points
4. Let you start sensor readings (real or simulated)

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
- **Professional UI**: Optimized interface for field use

## Troubleshooting

### Common Issues

**"No module named..." errors:**
- Ensure virtual environment is activated
- Re-run installation script
- Check Python version: `python --version`

**Hardware not detected:**
- Verify USB connection and MCP2221 drivers
- Check device permissions (macOS may require admin access)
- Application will run in simulation mode if hardware unavailable

**Application won't start:**
- Check console output for error messages
- Ensure all dependencies are installed
- Try running directly: `python OBS_Calibrator.py`

### Getting Help

1. Check console output for error messages
2. Verify all installation steps were completed
3. Ensure Python 3.12+ is installed and accessible
4. Try running in simulation mode first
5. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed help

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
├── build_installer.*         # Path 1: Build standalone app
├── install_dependencies.*    # Path 2: Install dependencies
├── run_from_source.*         # Path 2: Run from source
├── README.md                 # This file
└── TROUBLESHOOTING.md        # Detailed troubleshooting guide
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

**Note**: This application is designed for scientific use only. Always verify calibration results against known standards before field deployment.
