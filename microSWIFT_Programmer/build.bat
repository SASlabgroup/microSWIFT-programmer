@echo off
REM Convenience script to run the Windows build from root directory
cd /d "%~dp0"
call scripts\build\build_windows.bat %*
