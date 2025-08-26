@echo off
setlocal

REM microSWIFT_Programmer Windows Cleanup Script
REM This script removes all build artifacts and temporary files

echo =========================================
echo microSWIFT_Programmer Cleanup Script
echo =========================================
echo.

REM Get the project root directory (two levels up from scripts\clean\)
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%\..\.."

echo Cleaning build artifacts...
echo.

REM Remove PyInstaller build directories
if exist "build" (
    echo Removing build directory...
    rmdir /s /q build
)

if exist "dist" (
    echo Removing dist directory...
    rmdir /s /q dist
)

REM Remove Python cache directories
if exist "__pycache__" (
    echo Removing __pycache__ directory...
    rmdir /s /q __pycache__
)

REM Remove compiled Python files
echo Removing compiled Python files...
del /s /q *.pyc 2>nul
del /s /q *.pyo 2>nul

REM Remove all __pycache__ directories recursively
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

REM Remove virtual environments
if exist ".venv" (
    echo Removing virtual environment...
    rmdir /s /q .venv
)

if exist "venv" (
    echo Removing venv directory...
    rmdir /s /q venv
)

REM Remove executable files
if exist "*.exe" (
    echo Removing executable files...
    del /f /q *.exe
)

REM Remove launcher scripts created by build
if exist "run_microSWIFT_Programmer.bat" (
    echo Removing run_microSWIFT_Programmer.bat...
    del /f /q run_microSWIFT_Programmer.bat
)

if exist "microSWIFT_Programmer_Source.vbs" (
    echo Removing microSWIFT_Programmer_Source.vbs...
    del /f /q microSWIFT_Programmer_Source.vbs
)

REM Remove log files
echo Removing log files...
del /s /q *.log 2>nul

REM Remove PyInstaller work files
if exist "*.spec.bak" (
    echo Removing spec backup files...
    del /f /q *.spec.bak
)

REM Remove NSIS installer files
if exist "installer.nsi" (
    echo Removing NSIS installer script...
    del /f /q installer.nsi
)

REM Remove Python egg-info directories
for /d %%i in (*egg-info) do (
    echo Removing %%i...
    rmdir /s /q "%%i"
)

REM Optional: Remove downloaded firmware (uncomment if desired)
REM if exist "firmware\microSWIFT_V2.2.elf" (
REM     echo Removing downloaded firmware...
REM     del /f /q "firmware\microSWIFT_V2.2.elf"
REM )

echo.
echo =========================================
echo Cleanup completed!
echo =========================================
echo.
echo The following items have been removed:
echo   - Build and dist directories
echo   - Python cache and compiled files
echo   - Virtual environments
echo   - Executable files
echo   - Launcher scripts
echo   - Log files
echo   - Installer files
echo.
echo Source files and configurations have been preserved.
echo.
pause
