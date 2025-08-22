@echo off
REM OBS Calibrator - Windows Build Script
REM This script builds a standalone .exe installer using PyInstaller

setlocal EnableDelayedExpansion

echo ===============================================
echo OBS Calibrator - Windows Build Script
echo ===============================================
echo.

REM Check if virtual environment exists
echo [1/6] Checking virtual environment...
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found at 'venv\'
    echo Please run the installation script first:
    echo   install_windows.bat
    echo.
    pause
    exit /b 1
)
echo Virtual environment found

REM Check if main files exist
echo [2/6] Checking source files...
if not exist "OBS_Calibrator.py" (
    echo ERROR: OBS_Calibrator.py not found
    echo Make sure you're in the correct directory
    pause
    exit /b 1
)

if not exist "OBS_Calibrator.spec" (
    echo ERROR: OBS_Calibrator.spec not found
    echo PyInstaller spec file is missing
    pause
    exit /b 1
)
echo Source files found

REM Activate virtual environment
echo [3/6] Activating virtual environment...
call venv\Scripts\activate.bat
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Check PyInstaller installation
echo [4/6] Checking PyInstaller installation...
python -c "import PyInstaller; print('PyInstaller version:', PyInstaller.__version__)" 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: PyInstaller not found in virtual environment
    echo Installing PyInstaller...
    pip install pyinstaller
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to install PyInstaller
        pause
        call venv\Scripts\deactivate.bat
        exit /b 1
    )
)

REM Clean previous builds
echo [5/6] Cleaning previous builds...
if exist "build" (
    echo Removing old build directory...
    rmdir /s /q build
)
if exist "dist" (
    echo Removing old dist directory...
    rmdir /s /q dist
)

REM Build with PyInstaller
echo [6/6] Building executable with PyInstaller...
echo This may take several minutes...
echo.

pyinstaller --clean OBS_Calibrator.spec

set BUILD_EXIT_CODE=%ERRORLEVEL%

REM Check build result
if %BUILD_EXIT_CODE% neq 0 (
    echo.
    echo ===============================================
    echo BUILD FAILED!
    echo ===============================================
    echo.
    echo PyInstaller exited with error code: %BUILD_EXIT_CODE%
    echo Check the output above for detailed error information
    echo.
    echo Common issues:
    echo - Missing dependencies: Check requirements.txt
    echo - QML files not found: Verify file paths in spec file
    echo - Import errors: Check hidden imports in spec file
    echo.
    call venv\Scripts\deactivate.bat
    pause
    exit /b 1
)

REM Verify build output
if not exist "dist\OBS_Calibrator" (
    echo.
    echo ERROR: Build directory not created
    echo Check PyInstaller output for errors
    call venv\Scripts\deactivate.bat
    pause
    exit /b 1
)

if not exist "dist\OBS_Calibrator\OBS_Calibrator.exe" (
    echo.
    echo ERROR: Executable not created
    echo Check PyInstaller output for errors
    call venv\Scripts\deactivate.bat
    pause
    exit /b 1
)

echo.
echo ===============================================
echo BUILD SUCCESSFUL!
echo ===============================================
echo.
echo Built files location: dist\OBS_Calibrator\
echo Main executable: dist\OBS_Calibrator\OBS_Calibrator.exe
echo.

REM Get file size for user info
for %%A in ("dist\OBS_Calibrator\OBS_Calibrator.exe") do (
    set FILE_SIZE=%%~zA
)
set /a FILE_SIZE_MB=!FILE_SIZE! / 1048576
echo Executable size: ~!FILE_SIZE_MB! MB
echo.

echo To test the build:
echo   cd dist\OBS_Calibrator
echo   OBS_Calibrator.exe
echo.
echo To distribute:
echo   1. Copy the entire 'dist\OBS_Calibrator' folder
echo   2. Or create an installer using NSIS/Inno Setup
echo   3. Users can run OBS_Calibrator.exe directly
echo.

echo The standalone executable includes all dependencies
echo and will run on Windows systems without Python installed.
echo.

call venv\Scripts\deactivate.bat

echo Build completed successfully!
pause
