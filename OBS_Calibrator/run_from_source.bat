@echo off
REM OBS Calibrator - Source Runner (Windows)
REM This script runs the application from source with proper virtual environment handling

setlocal enabledelayedexpansion

echo ==============================================
echo       OBS Calibrator - Running from Source
echo ==============================================
echo.

REM Check if we're in the right directory
if not exist "OBS_Calibrator.py" (
    echo [ERROR] OBS_Calibrator.py not found!
    echo Please run this script from the OBS_Calibrator directory.
    echo.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo [ERROR] Virtual environment not found!
    echo.
    echo Please run the dependency installer first:
    echo   install_dependencies.bat
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment!
    echo Try reinstalling dependencies:
    echo   install_dependencies.bat
    echo.
    pause
    exit /b 1
)

echo [SUCCESS] Virtual environment activated

REM Check if required packages are installed
echo [INFO] Checking dependencies...
python -c "import PySide6, matplotlib, numpy, sklearn" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Required dependencies are missing!
    echo.
    echo Please reinstall dependencies:
    echo   install_dependencies.bat
    echo.
    call venv\Scripts\deactivate.bat
    pause
    exit /b 1
)

echo [SUCCESS] Dependencies verified

REM Run the application
echo [INFO] Starting OBS Calibrator...
echo.

REM Run the Python application
python OBS_Calibrator.py

REM Capture the exit code
set APP_EXIT_CODE=%errorlevel%

REM Always deactivate virtual environment
echo.
echo [INFO] Cleaning up...
call venv\Scripts\deactivate.bat

REM Show exit status
if %APP_EXIT_CODE% equ 0 (
    echo [SUCCESS] Application exited normally
) else (
    echo [WARNING] Application exited with code %APP_EXIT_CODE%
)

echo.
pause
