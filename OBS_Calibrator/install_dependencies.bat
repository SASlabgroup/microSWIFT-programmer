@echo off
REM OBS Calibrator - Dependency Installer (Windows)
REM This script installs all required dependencies for running from source

setlocal enabledelayedexpansion

echo ==============================================
echo     OBS Calibrator - Dependency Installer
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

REM Check if we're in the right directory
if not exist "OBS_Calibrator.py" (
    echo [ERROR] OBS_Calibrator.py not found!
    echo Please run this script from the OBS_Calibrator directory.
    echo.
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment!
        echo Please ensure Python is properly installed.
        echo.
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created
) else (
    echo [INFO] Virtual environment already exists
)

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

REM Test the installation
echo [INFO] Testing installation...
python -c "import PySide6; print('PySide6:', PySide6.__version__)" 2>nul
python -c "import matplotlib; print('matplotlib:', matplotlib.__version__)" 2>nul
python -c "import numpy; print('numpy:', numpy.__version__)" 2>nul  
python -c "import sklearn; print('scikit-learn:', sklearn.__version__)" 2>nul

REM Deactivate virtual environment
call venv\Scripts\deactivate.bat

echo.
echo ==============================================
echo [SUCCESS] Dependencies installed successfully!
echo ==============================================
echo.
echo You can now run the application using:
echo   run_from_source.bat
echo.
echo Or manually:
echo   venv\Scripts\activate.bat
echo   python OBS_Calibrator.py
echo   venv\Scripts\deactivate.bat
echo.
pause
