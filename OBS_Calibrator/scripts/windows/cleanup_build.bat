@echo off
REM OBS Calibrator - Build Cleanup Script
REM Removes unnecessary files after building the installer

setlocal enabledelayedexpansion

echo ==============================================
echo     OBS Calibrator - Build Cleanup
echo ==============================================
echo.

REM Get the project root directory
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

REM Calculate space used before cleanup
echo [INFO] Calculating space usage before cleanup...
for /f "tokens=1-2" %%a in ('dir /-c ^| find "bytes"') do (
    set BEFORE_SIZE=%%a
)
echo Current directory size: %BEFORE_SIZE% bytes
echo.

REM Ask for confirmation
echo This script will remove the following items:
echo   1. Virtual environment (venv\)
echo   2. Build artifacts (build\)
echo   3. Python cache (__pycache__\)
echo   4. Unpacked distribution files (dist\OBS_Calibrator\)
echo.
echo It will KEEP:
echo   - Your source code files
echo   - The final .exe package
echo   - Configuration and documentation files
echo.

set /p CONFIRM="Do you want to proceed with cleanup? (y/N): "
if /i not "%CONFIRM%"=="y" (
    echo [WARNING] Cleanup cancelled
    pause
    exit /b 0
)

echo.

REM Remove virtual environment
if exist "venv" (
    echo [INFO] Removing virtual environment...
    rmdir /s /q venv
    echo [SUCCESS] Virtual environment removed
) else (
    echo [WARNING] Virtual environment not found
)

REM Remove build directory
if exist "build" (
    echo [INFO] Removing build artifacts...
    rmdir /s /q build
    echo [SUCCESS] Build artifacts removed
) else (
    echo [WARNING] Build directory not found
)

REM Remove Python cache
if exist "__pycache__" (
    echo [INFO] Removing Python cache...
    rmdir /s /q __pycache__
    echo [SUCCESS] Python cache removed
) else (
    echo [WARNING] Python cache not found
)

REM Remove unpacked distribution (but keep .exe)
if exist "dist\OBS_Calibrator" (
    REM Check if this is just the unpacked folder (not the exe location)
    if exist "dist\OBS_Calibrator.exe" (
        echo [INFO] Keeping executable distribution
    ) else (
        echo [INFO] Removing unpacked distribution files...
        rmdir /s /q "dist\OBS_Calibrator"
        echo [SUCCESS] Unpacked distribution removed
    )
)

REM Remove any .pyc files
echo [INFO] Removing compiled Python files...
del /s /q *.pyc 2>nul
del /s /q *.pyo 2>nul
echo [SUCCESS] Compiled Python files removed

echo.
echo [INFO] Calculating space usage after cleanup...
for /f "tokens=1-2" %%a in ('dir /-c ^| find "bytes"') do (
    set AFTER_SIZE=%%a
)
echo Current directory size: %AFTER_SIZE% bytes

echo.
echo ==============================================
echo [SUCCESS] Cleanup completed successfully!
echo ==============================================
echo.
echo Space before cleanup: %BEFORE_SIZE% bytes
echo Space after cleanup:  %AFTER_SIZE% bytes
echo.
echo To rebuild the application, run:
echo   build_installer.bat
echo.
pause
