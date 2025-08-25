@echo off
REM Convenience script to run the build installer from the project root
cd /d "%~dp0" && call scripts\windows\build_installer.bat %*
