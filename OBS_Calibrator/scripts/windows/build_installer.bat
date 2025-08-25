@echo off
REM OBS Calibrator - Automated Installer (Windows)
REM This script sets up the development environment and builds a standalone application

setlocal enabledelayedexpansion

echo ==============================================
echo     OBS Calibrator - Automated Installer
echo ==============================================
echo.

REM Check for Python installation
echo [INFO] Checking Python installation...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.12 or higher from:
    echo   https://www.python.org/downloads/
    echo.
    echo During installation, make sure to check "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i

REM Extract major and minor version numbers
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set PYTHON_MAJOR=%%a
    set PYTHON_MINOR=%%b
)

REM Check if Python version is 3.12 or higher
if %PYTHON_MAJOR% lss 3 (
    echo [ERROR] Python %PYTHON_VERSION% detected. Python 3.12+ is required!
    echo Please upgrade Python from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

if %PYTHON_MAJOR% equ 3 if %PYTHON_MINOR% lss 12 (
    echo [ERROR] Python %PYTHON_VERSION% detected. Python 3.12+ is required!
    echo Please upgrade Python from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [SUCCESS] Python %PYTHON_VERSION% detected

REM Get the project root directory (two levels up from scripts\windows\)
set "SCRIPT_DIR=%~dp0"
for %%A in ("%SCRIPT_DIR%..\..\.") do set "PROJECT_ROOT=%%~fA"
cd /d "%PROJECT_ROOT%"

REM Check if we're in the right directory
if not exist "src\OBS_Calibrator.py" (
    echo [ERROR] src\OBS_Calibrator.py not found!
    echo Project structure error. Expected to find src\OBS_Calibrator.py
    echo.
    pause
    exit /b 1
)

REM Create virtual environment
echo [INFO] Creating virtual environment...
if exist "venv" (
    echo [WARNING] Virtual environment already exists. Removing...
    rmdir /s /q venv
)

python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment!
    echo Please ensure Python is properly installed.
    echo.
    pause
    exit /b 1
)

echo [SUCCESS] Virtual environment created

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo [INFO] Installing Python dependencies...
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found!
    pause
    exit /b 1
)

pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies!
    echo Please check the requirements.txt file and try again.
    echo.
    pause
    exit /b 1
)

echo [SUCCESS] Dependencies installed successfully

REM Build application with PyInstaller
echo [INFO] Building standalone application...
if not exist "build_config\OBS_Calibrator.spec" (
    echo [ERROR] build_config\OBS_Calibrator.spec not found!
    pause
    exit /b 1
)

pyinstaller --noconfirm build_config\OBS_Calibrator.spec
if %errorlevel% neq 0 (
    echo [ERROR] Failed to build application!
    echo Check the console output above for details.
    echo.
    pause
    exit /b 1
)

echo [SUCCESS] Application built successfully

REM Check what was built
if exist "dist\OBS_Calibrator\OBS_Calibrator.exe" (
    echo [SUCCESS] Windows Application built: dist\OBS_Calibrator\
    echo.
    echo To run the application:
    echo   1. Open File Explorer and navigate to the project directory
    echo   2. Go to the 'dist\OBS_Calibrator' folder
    echo   3. Double-click 'OBS_Calibrator.exe'
    echo.
    echo Or from command prompt:
    echo   dist\OBS_Calibrator\OBS_Calibrator.exe
) else (
    echo [WARNING] Application built but location unclear. Check the dist\ directory.
)

REM Deactivate virtual environment
call venv\Scripts\deactivate.bat

echo.
echo ==============================================
echo [SUCCESS] Build completed successfully!
echo ==============================================
echo.

REM Offer to clean up build artifacts
echo The application has been built successfully.
echo.
echo Would you like to clean up build artifacts to save disk space?
echo This will remove:
echo   - Virtual environment (venv\)
echo   - Build files (build\)
echo   - Python cache (__pycache__\)
echo   - Temporary distribution files
echo.
echo This will KEEP your application and source code.
echo.

set /p CLEANUP="Clean up build artifacts? (y/N): "
if /i "%CLEANUP%"=="y" (
    echo.
    echo [INFO] Starting cleanup...
    
    REM Remove virtual environment
    if exist "venv" (
        echo [INFO] Removing virtual environment...
        rmdir /s /q venv
    )
    
    REM Remove build directory
    if exist "build" (
        echo [INFO] Removing build artifacts...
        rmdir /s /q build
    )
    
    REM Remove Python cache
    if exist "__pycache__" (
        echo [INFO] Removing Python cache...
        rmdir /s /q __pycache__
    )
    
    REM Remove any .pyc files
    echo [INFO] Removing compiled Python files...
    del /s /q *.pyc 2>nul
    del /s /q *.pyo 2>nul
    
    echo.
    echo [SUCCESS] Cleanup completed!
) else (
    echo [INFO] Skipping cleanup. You can run cleanup_build.bat later if needed.
)

echo.
echo ==============================================
echo [SUCCESS] Installation completed successfully!
echo ==============================================
echo.
echo What happens next:
echo   1. The standalone application is ready to use
echo   2. No Python environment needed to run the app
echo   3. The app will work on similar systems without installation
echo.
echo If you need to run from source instead, use:
echo   run_from_source.bat
echo.
pause
