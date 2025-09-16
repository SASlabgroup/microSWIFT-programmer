@echo off
setlocal enabledelayedexpansion

REM microSWIFT_Programmer Run-from-Source Script for Windows
REM This script runs the application directly from source code

echo =========================================
echo microSWIFT Programmer - Run from Source
echo =========================================
echo.

REM Get the project root directory (two levels up from scripts\run\)
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%\..\.."

REM Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Check Python version
echo Python version:
python --version
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    echo Virtual environment created
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import PyQt6" 2>nul
if %errorlevel% neq 0 (
    echo Installing dependencies...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    echo Dependencies installed
    echo.
) else (
    echo Dependencies already installed
    echo.
)

REM Check if STM32CubeProgrammer is installed (Windows)
set "PROGRAMMER_PATH=C:\Program Files\STMicroelectronics\STM32Cube\STM32CubeProgrammer"
if not exist "%PROGRAMMER_PATH%" (
    echo Warning: STM32CubeProgrammer not found at expected location
    echo Please install STM32CubeProgrammer from:
    echo https://www.st.com/en/development-tools/stm32cubeprog.html
    echo.
)

REM Run the application
echo Starting microSWIFT Programmer...
echo =========================================
echo.

REM Pass all command line arguments to the Python script
python src\microSWIFT_Programmer.py %*

REM Capture the exit code
set EXIT_CODE=%errorlevel%

REM Deactivate virtual environment
call deactivate

REM If no command line arguments were provided (double-clicked), keep window open
if "%~1"=="" (
    echo.
    echo =========================================
    echo Application closed
    pause
)

REM Exit with the same code as the Python script
exit /b %EXIT_CODE%
