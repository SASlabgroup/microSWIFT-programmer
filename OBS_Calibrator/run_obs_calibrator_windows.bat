@echo off
REM OBS Calibrator - Windows Launcher Script
REM This script activates the virtual environment and launches the application

setlocal EnableDelayedExpansion

echo ===============================================
echo OBS Calibrator - Windows Launcher
echo ===============================================
echo.

REM Check if virtual environment exists
echo [1/3] Checking virtual environment...
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found at 'venv\'
    echo Please run the installation script first:
    echo   install_windows.bat
    echo.
    pause
    exit /b 1
)
echo Virtual environment found

REM Check if main application exists
echo [2/3] Checking application files...
if not exist "OBS_Calibrator.py" (
    echo ERROR: OBS_Calibrator.py not found
    echo Make sure you're running this script from the OBS_Calibrator directory
    echo.
    pause
    exit /b 1
)
echo Application files found

REM Activate virtual environment
echo [3/3] Activating virtual environment and launching application...
call venv\Scripts\activate.bat
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to activate virtual environment
    echo Try running the installation script again:
    echo   install_windows.bat
    echo.
    pause
    exit /b 1
)

echo.
echo Starting OBS Calibrator...
echo Close this window to stop the application
echo ===============================================
echo.

REM Launch the application with error handling
python OBS_Calibrator.py
set APP_EXIT_CODE=%ERRORLEVEL%

REM Cleanup and deactivate
echo.
echo ===============================================
echo Application closed
echo ===============================================

REM Check exit code
if %APP_EXIT_CODE% neq 0 (
    echo.
    echo Application exited with error code: %APP_EXIT_CODE%
    echo Check the output above for error details
    echo.
    echo Common issues:
    echo - Missing dependencies: Re-run install_windows.bat
    echo - Hardware connection problems: Check USB connections
    echo - Qt/GUI issues: Try running from command line for detailed output
    echo.
) else (
    echo Application exited normally
)

REM Deactivate virtual environment
call venv\Scripts\deactivate.bat 2>nul

echo Virtual environment deactivated
echo.
pause
