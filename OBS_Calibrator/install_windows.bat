@echo off
REM OBS Calibrator - Windows Installation Script
REM This script creates a virtual environment and installs all dependencies

echo ===============================================
echo OBS Calibrator - Windows Installation
echo ===============================================
echo.

REM Check if Python is installed
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.13 or higher from https://python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

REM Check Python version
echo [1/5] Verifying Python version...
for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo Found Python version: %PYTHON_VERSION%

REM Check if version is 3.13 or higher (basic check)
echo %PYTHON_VERSION% | findstr /R "^3\.1[3-9]\|^3\.[2-9][0-9]\|^[4-9]\." >nul
if %ERRORLEVEL% neq 0 (
    echo WARNING: Python 3.13 or higher is recommended
    echo Current version: %PYTHON_VERSION%
    echo Continue anyway? (y/N)
    set /p CONTINUE=
    if /i not "%CONTINUE%"=="y" (
        echo Installation cancelled
        pause
        exit /b 1
    )
)

echo [2/5] Removing existing virtual environment (if any)...
if exist "venv" (
    rmdir /s /q venv
    echo Removed existing virtual environment
)

echo [3/5] Creating new virtual environment...
python -m venv venv
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to create virtual environment
    echo Make sure you have venv module installed: pip install virtualenv
    echo.
    pause
    exit /b 1
)
echo Virtual environment created successfully

echo [4/5] Activating virtual environment and upgrading pip...
call venv\Scripts\activate.bat
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to activate virtual environment
    echo.
    pause
    exit /b 1
)

echo Upgrading pip...
python -m pip install --upgrade pip
if %ERRORLEVEL% neq 0 (
    echo WARNING: Failed to upgrade pip, continuing with existing version
)

echo [5/5] Installing dependencies from requirements.txt...
if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found
    echo Make sure you're running this script from the OBS_Calibrator directory
    echo.
    pause
    call venv\Scripts\deactivate.bat
    exit /b 1
)

pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install dependencies
    echo Check your internet connection and try again
    echo.
    pause
    call venv\Scripts\deactivate.bat
    exit /b 1
)

echo.
echo ===============================================
echo Installation completed successfully!
echo ===============================================
echo.
echo Virtual environment created at: venv\
echo All dependencies installed from requirements.txt
echo.
echo To launch OBS Calibrator, run:
echo   run_obs_calibrator_windows.bat
echo.
echo To manually activate the environment:
echo   venv\Scripts\activate.bat
echo   python OBS_Calibrator.py
echo.

call venv\Scripts\deactivate.bat
pause
