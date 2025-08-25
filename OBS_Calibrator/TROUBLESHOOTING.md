# OBS Calibrator - Troubleshooting Guide

## Installation Issues

### 🔧 Python Not Found

**Error:** `python: command not found` or `Python is not installed`

**Solutions:**

**Windows:**
1. Download Python 3.13 from [python.org](https://python.org/downloads/)
2. **IMPORTANT:** Check "Add Python to PATH" during installation
3. Restart Command Prompt after installation
4. Test with: `python --version`

**macOS:**
1. Install Homebrew: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
2. Install Python: `brew install python@3.13`
3. Test with: `python3 --version`

### 🔧 Virtual Environment Creation Failed

**Error:** `Failed to create virtual environment`

**Solutions:**

**Linux/Ubuntu:**
```bash
sudo apt update
sudo apt install python3-venv python3-dev
```

**macOS:**
- Virtual environment should work out of the box with Python 3.13+
- If issues persist, try: `brew install python@3.13`

**Windows:**
- Ensure Python was installed with "Add to PATH" option
- Try running Command Prompt as Administrator

### 🔧 Permission Errors (macOS/Linux)

**Error:** `Permission denied` when running scripts

**Solution:**
```bash
# For quick access scripts in root
chmod +x build.sh

# For all scripts in their directories
chmod +x scripts/unix/*.sh
```

### 🔧 Build Script Fails

**Error:** PyInstaller build fails

**Possible Solutions:**
1. **Free up disk space** (build needs ~2GB temporarily)
2. **Use the cleanup script:**
   ```bash
   ./scripts/unix/cleanup_build.sh  # macOS/Linux
   scripts\windows\cleanup_build.bat   # Windows
   ```
3. **Manual clean and retry:**
   ```bash
   rm -rf venv build dist __pycache__
   ./build.sh  # or ./scripts/unix/build_installer.sh
   ```
4. **Try Path 2 instead:**
   ```bash
   ./scripts/unix/install_dependencies.sh
   ./scripts/unix/run_from_source.sh
   ```

### 🔧 Disk Space Issues

**Error:** "No space left on device" or build uses too much space

**Solutions:**

1. **Use automatic cleanup during build:**
   - When `build_installer` completes, answer "y" to cleanup prompt
   - This removes ~2GB of temporary build files
   - Your app is preserved in the `dist` folder

2. **Run cleanup manually:**
   ```bash
   # macOS/Linux
   ./scripts/unix/cleanup_build.sh
   
   # Windows
   scripts\windows\cleanup_build.bat
   ```

3. **What cleanup removes:**
   - Virtual environment (`venv/`) - can be recreated
   - Build artifacts (`build/`) - temporary files
   - Python cache (`__pycache__/`) - regenerated automatically
   - Unpacked files in `dist/` - keeping only the final app
   - **Saves approximately 2GB of disk space**

4. **What cleanup keeps:**
   - Your source code files
   - The final application (.app on Mac, .exe on Windows)
   - Configuration files
   - Documentation

## Application Issues

### 🔧 App Won't Start

**Symptoms:** Double-clicking does nothing or app crashes immediately

**Solutions:**

1. **Check from terminal:**
   ```bash
   # macOS
   ./dist/OBS_Calibrator.app/Contents/MacOS/OBS_Calibrator
   
   # Windows
   dist\OBS_Calibrator\OBS_Calibrator.exe
   ```

2. **Look for error messages** in the terminal output

3. **Try running from source:**
   ```bash
   ./scripts/unix/run_from_source.sh  # macOS/Linux
   scripts\windows\run_from_source.bat   # Windows
   ```

### 🔧 Dark Theme Issues

**Symptoms:** Text is hard to read, colors look wrong

**Solutions:**
- This is usually a Windows-specific issue
- The app enforces dark theme, but some systems may override it
- Try running from source to see if the issue persists
- Check your system's display scaling settings

### 🔧 Hardware Detection Issues

**Symptoms:** App shows "No Device!" when hardware is connected

**Solutions:**

1. **Check USB connection:**
   - Ensure MCP2221 board is properly connected
   - Try a different USB cable/port

2. **Verify hardware detection:**
   ```bash
   # macOS - check if device appears
   system_profiler SPUSBDataType | grep MCP2221
   
   # Windows - check Device Manager
   # Look for "MCP2221 USB-I2C/UART Combo"
   ```

3. **Driver issues (Windows):**
   - Download MCP2221 drivers from Microchip
   - Install and restart

4. **Permission issues (Linux):**
   ```bash
   # Add your user to dialout group
   sudo usermod -a -G dialout $USER
   # Log out and log back in
   ```

### 🔧 Sensor Reading Issues

**Symptoms:** Hardware detected but readings seem wrong

**Solutions:**
1. **Check sensor connections** - ensure VCNL4010 is properly wired to MCP2221
2. **Test in simulation mode** first to verify app functionality
3. **Check I2C address** - VCNL4010 default is 0x13
4. **Try different sensor** if available

## Script-Specific Issues

### 🔧 Script Not Found

**Error:** `No such file or directory` when running scripts

**Solution:**
```bash
# Scripts are now in subdirectories:
./scripts/unix/build_installer.sh    # macOS/Linux
scripts\windows\build_installer.bat  # Windows

# Or use convenience scripts from root:
./build.sh    # macOS/Linux
build.bat     # Windows
```

### 🔧 install_dependencies Script Fails

**Common fixes:**
```bash
# Clean start
rm -rf venv
./scripts/unix/install_dependencies.sh

# Check Python version
python3 --version  # Should be 3.12+

# Manual installation from project root
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 🔧 run_from_source Script Fails

**Error:** `Virtual environment not found`
**Solution:** Run `./scripts/unix/install_dependencies.sh` first

**Error:** `src/OBS_Calibrator.py not found`
**Solution:** Make sure you're in the project root directory

**Error:** `Required dependencies are missing`
**Solution:** 
```bash
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

## Windows-Specific Issues

### 🔧 Batch Files Won't Run

**Symptoms:** Double-clicking .bat files opens them in text editor

**Solution:**
1. Navigate to `scripts\windows\` folder
2. Right-click the .bat file
3. Select "Open with" → "Command Prompt"
4. Or from Command Prompt: `cd scripts\windows && install_dependencies.bat`

### 🔧 PowerShell Execution Policy

**Error:** `cannot be loaded because running scripts is disabled`

**Solution:**
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Getting Help

If you're still having issues:

1. **Check the console output** for specific error messages
2. **Try the alternative installation path** (if Path 1 fails, try Path 2)
3. **Test in simulation mode** to isolate hardware vs software issues
4. **Check system requirements:**
   - Python 3.12+ installed and in PATH
   - At least 2GB free disk space for building (can be reclaimed with cleanup)
   - Administrative privileges may be needed for some operations
5. **Low on disk space?** Run `scripts/[platform]/cleanup_build.*` to free up ~2GB after building

## Quick Reference

### Script Locations
- **Quick access from root:** `build.sh` / `build.bat`
- **Platform scripts:** `scripts/unix/*.sh` or `scripts\windows\*.bat`
- **Source code:** `src/` directory
- **UI files:** `ui/` directory
- **Build config:** `build_config/` directory

### File Purposes
- `scripts/[platform]/build_installer.*` → Creates standalone app with cleanup (Path 1)
- `scripts/[platform]/install_dependencies.*` → Sets up Python environment (Path 2)
- `scripts/[platform]/run_from_source.*` → Runs app from source code (Path 2)
- `scripts/[platform]/cleanup_build.*` → Removes build artifacts to save ~2GB

### Recommended Installation Order
1. Try `build.sh` or `build.bat` first (creates standalone app)
2. If that fails, use Path 2 scripts in `scripts/[platform]/`
3. Both approaches work, Path 1 is more user-friendly, Path 2 is more reliable
