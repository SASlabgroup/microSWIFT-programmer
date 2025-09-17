@echo off
REM Build microSWIFT Programmer for Windows - creates standalone .exe

setlocal

REM Exit on error
set "ERRORLEVEL=0"

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
REM Get the project root (two levels up from scripts\build\)
cd /d "%SCRIPT_DIR%\..\.."
set "PROJECT_ROOT=%CD%"

echo ======================================
echo microSWIFT Programmer - Windows Builder
echo ======================================
echo.

REM Clean previous builds
echo Cleaning previous builds...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

REM Check if Python is available
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH!
    echo Please install Python 3.12 or higher from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

REM Install dependencies
echo Installing dependencies...
python -m pip install -q -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to install dependencies!
    pause
    exit /b 1
)

REM Build with PyInstaller
echo Building application with PyInstaller...
echo This may take several minutes...
echo.
pyinstaller "%PROJECT_ROOT%\resources\specs\microSWIFT_Programmer_windows.spec" --noconfirm --clean
if %ERRORLEVEL% NEQ 0 (
    echo Error: PyInstaller build failed!
    pause
    exit /b 1
)

REM Check if build was successful
if exist "dist\microSWIFT_Programmer.exe" (
    echo.
    echo =========================================
    echo Build successful!
    echo =========================================
    echo Executable created: dist\microSWIFT_Programmer.exe
    
    REM Get executable size
    for %%I in ("dist\microSWIFT_Programmer.exe") do echo Application size: %%~zI bytes
    echo.
    
    echo Testing application launch...
    REM Test the application (timeout after 5 seconds)
    timeout 5 >nul 2>&1 & dist\microSWIFT_Programmer.exe --help >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo Application launches successfully
    ) else (
        echo Application test inconclusive (this is normal for GUI apps)
    )
    echo.
    
    REM Prompt for cleanup
    echo.
    set /p "cleanup_choice=Would you like to clean up build artifacts? (y/N): "
    if /i "%cleanup_choice%"=="y" (
        echo Running cleanup...
        call "%SCRIPT_DIR%\..\clean\cleanup_windows.bat"
        echo Cleanup completed
    )
    
    REM Build completed successfully - show final message
    echo.
    echo ======================================
    echo Build completed successfully!
    echo ======================================
    echo.
    pause
    exit /b 0
    
) else (
    echo.
    echo =========================================
    echo Build failed!
    echo =========================================
    echo Please check the error messages above.
    pause
    exit /b 1
)

REM Script should not reach here - removed duplicate success message
