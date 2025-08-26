# microSWIFT Programmer Troubleshooting Guide

This guide helps resolve common issues with building and running the microSWIFT Programmer application.

## Table of Contents
- [Build Issues](#build-issues)
- [Runtime Issues](#runtime-issues)
- [Platform-Specific Issues](#platform-specific-issues)
- [STM32CubeProgrammer Issues](#stm32cubeprogrammer-issues)
- [Python Dependencies](#python-dependencies)

## Build Issues

### PyInstaller Build Fails

**Problem:** PyInstaller fails with import errors or module not found errors.

**Solution:**
1. Ensure you're using Python 3.12 or higher:
   ```bash
   python3 --version
   ```
2. Clean the build environment:
   ```bash
   # macOS/Linux
   ./cleanup_macos.sh
   
   # Windows
   cleanup_windows.bat
   ```
3. Reinstall dependencies in a fresh virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### "Module not found" Errors

**Problem:** Missing Python modules during build or runtime.

**Solution:**
- Ensure all dependencies are installed:
  ```bash
  pip install PyQt6 pyserial requests pyinstaller
  ```
- If specific modules are missing, install them individually:
  ```bash
  pip install <module_name>
  ```

### Build Creates Large Executables

**Problem:** The built application is unexpectedly large (>500MB).

**Solution:**
- This is normal for PyInstaller bundles with PyQt6
- The spec files already exclude unnecessary packages
- To further reduce size, you can modify the spec file's `excludes` list

## Runtime Issues

### Application Won't Start

**Problem:** Double-clicking the app does nothing or crashes immediately.

**Solution:**
1. Run from terminal to see error messages:
   ```bash
   # macOS
   ./dist/microSWIFT_Programmer.app/Contents/MacOS/microSWIFT_Programmer
   
   # Windows
   dist\microSWIFT_Programmer.exe
   ```
2. Check for missing resources:
   - Ensure `firmware/` directory exists with required `.bin` files
   - Verify `resources/images/microSWIFT_pic.png` exists

### "STLink V3 not found" Error

**Problem:** Application can't detect the STLink programmer.

**Solution:**
1. Verify STLink is connected via USB
2. Check device drivers are installed:
   - **Windows:** Install STLink drivers from ST website
   - **macOS:** No drivers needed, but check System Preferences > Security & Privacy
3. Try a different USB port or cable
4. Verify STLink appears in device list:
   ```bash
   # macOS/Linux
   ls /dev/tty.*
   
   # Windows (in Device Manager)
   Check under "Universal Serial Bus devices"
   ```

### Firmware Download Fails

**Problem:** "Unable to pull firmware from GitHub!" error on startup.

**Solution:**
1. Check internet connection
2. Verify GitHub is accessible
3. Run with `--no_firmware_update` flag:
   ```bash
   ./microSWIFT_Programmer --no_firmware_update
   ```
4. Manually download firmware:
   - Visit: https://github.com/SASlabgroup/microSWIFT-V2-Binaries/tree/main/V2.2
   - Download `microSWIFT_V2.2.elf` to `firmware/` directory

### GUI Elements Missing or Misaligned

**Problem:** Interface elements don't appear correctly.

**Solution:**
1. Check display scaling settings
2. Try different Qt styles:
   ```bash
   QT_STYLE_OVERRIDE=fusion ./microSWIFT_Programmer
   ```
3. Verify PyQt6 version:
   ```bash
   pip show PyQt6
   ```

## Platform-Specific Issues

### macOS

#### "App is damaged" Error

**Problem:** macOS refuses to open the app.

**Solution:**
1. Remove quarantine attribute:
   ```bash
   xattr -cr dist/microSWIFT_Programmer.app
   ```
2. Or allow in System Preferences > Security & Privacy > General

#### App Doesn't Respond to Dark Mode

**Problem:** App appearance doesn't change with system theme.

**Solution:**
- This is a PyQt6 limitation on some macOS versions
- The app should still function normally

### Windows

#### Antivirus Blocks the Application

**Problem:** Windows Defender or antivirus flags the exe.

**Solution:**
1. Add exception for the application in antivirus settings
2. Or build from source using `run_from_source.bat`

#### Missing VCRUNTIME DLLs

**Problem:** Error about missing Visual C++ runtime.

**Solution:**
- Install Visual C++ Redistributables from Microsoft:
  https://support.microsoft.com/en-us/help/2977003/

## STM32CubeProgrammer Issues

### "STM32CubeProgrammer not found" Error

**Problem:** Application can't find STM32CubeProgrammer CLI.

**Solution:**
1. Install STM32CubeProgrammer from ST website:
   https://www.st.com/en/development-tools/stm32cubeprog.html
2. Verify installation path:
   - **macOS:** `/Applications/STMicroelectronics/STM32Cube/STM32CubeProgrammer/`
   - **Windows:** `C:\Program Files\STMicroelectronics\STM32Cube\STM32CubeProgrammer\`
3. Add to PATH if installed elsewhere

### Programming Fails

**Problem:** "Programming Failed with code X" error.

**Solution:**
1. Check device connections:
   - Ensure target device is powered
   - Verify SWD connections are correct
   - Try lower SWD frequency
2. Check target device state:
   - Device may be in sleep/low-power mode
   - Try hardware reset while connecting
3. Verify firmware files:
   - `microSWIFT_V2.2.elf` exists and is not corrupted
   - `config.bin` is properly generated
   - `zeros_64k.bin` exists in firmware directory

## Python Dependencies

### PyQt6 Installation Fails

**Problem:** Can't install PyQt6 via pip.

**Solution:**
1. Upgrade pip first:
   ```bash
   python -m pip install --upgrade pip
   ```
2. Install wheel:
   ```bash
   pip install wheel
   ```
3. Try installing with no cache:
   ```bash
   pip install --no-cache-dir PyQt6
   ```

### Serial Port Issues

**Problem:** pyserial can't access ports.

**Solution:**
1. **Linux:** Add user to dialout group:
   ```bash
   sudo usermod -a -G dialout $USER
   ```
   Then logout and login again
2. **macOS:** Check for conflicting serial drivers
3. **Windows:** Ensure no other application is using the port

## Getting Help

If your issue isn't covered here:

1. Check the main README for basic setup instructions
2. Run the diagnostic command:
   ```bash
   python src/microSWIFT_Programmer.py --help
   ```
3. Check GitHub Issues: https://github.com/SASlabgroup/microSWIFT-programmer
4. Contact the development team with:
   - Your operating system and version
   - Python version (`python --version`)
   - Complete error message
   - Steps to reproduce the issue
