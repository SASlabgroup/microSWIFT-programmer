# OBS Calibrator - Changelog

## [Reorganization] - 2024-08-25

### Changed
- **Project Structure Overhaul**: Reorganized files into logical directories for better maintainability
  - Source code moved to `src/` directory
  - UI/QML files moved to `ui/` directory
  - Platform-specific scripts organized into `scripts/windows/` and `scripts/unix/`
  - Build configuration files moved to `build_config/` directory

### Added
- **Convenience Scripts**: Added `build.sh` and `build.bat` in project root for quick access
- **Automatic Cleanup**: Integrated cleanup functionality into build scripts with optional prompt
- **Cleanup Scripts**: Standalone cleanup scripts to remove build artifacts and save ~2GB disk space

### Fixed
- **UI Layout Issue**: Fixed window height mismatch that was hiding bottom controls (Serial Number field, buttons)
  - Adjusted component positions to fit within 800x800 pixel window
  - Fixed height consistency between Constants.qml and OBS_Calibrator_Screen.ui.qml

### Updated
- **Documentation**: Updated README.md and TROUBLESHOOTING.md to reflect new directory structure
- **Build Scripts**: All scripts updated to work from new locations
- **PyInstaller Spec**: Updated paths in OBS_Calibrator.spec for new structure
- **Python Imports**: Updated OBS_Calibrator.py to find UI files in new locations

### Benefits
- ✨ Cleaner root directory (10 items vs 20+)
- 📂 Logical file organization
- 🖥️ Clear platform separation
- 🔧 Easier maintenance
- 📦 Better for version control

### Migration Notes
- All functionality remains the same
- Use `build.sh`/`build.bat` from root or navigate to `scripts/[platform]/` for specific scripts
- Virtual environment still created in project root
- Build output still goes to `dist/` directory
