# microSWIFT-programmer

Installation:

1) [Install Python](https://www.python.org/downloads/)
2) In a terminal, install Python dependencies
```shell
python -m pip install --upgrade pip
python -m pip install PyQt6, PySerial, requests
```
3) Run the pyinstall script
```shell
python pyinstall.py
```
4) Once complete, the application executable will be in the "dist" folder
5) On a Mac, you can move "microSWIFT_programmer.app" to your Applications directory if desired.
   On Windows, the executable can be located wherever you'd like.

Notes:

The application lists the version number in the window top banner. This repo is set up to set the default branch to the most recent version of the program. Please ensure the version you are running on your local machine matches the version listed in the default branch within this repo.

[On startup, the application downloads the V2.2 firmware binary file "microSWIFT_V2.2.elf" to ensure the most recent copy of firmware is burned to the device. If the application is unable to download this file (network issue, etc.), an error will appear indicating so. If this is to occur, users must ensure the firmware]: #
