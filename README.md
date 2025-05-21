# microSWIFT-programmer

Installation and Usage:

1) [Install Python](https://www.python.org/downloads/)
2) [Install STM32CubeIDE (Create an account if needed)](https://www.st.com/en/development-tools/stm32cubeprog.html)
3) In a terminal, install Python dependencies
```shell
python -m pip install --upgrade pip
python -m pip install PyQt6, PySerial, requests
```
4) Clone or download this repo to a location of your choice
5) Open a terminal and navigate to where you cloned/downloaded this repo
6) Run the program
```shell
python microSWIFT_programmer.py
```

Notes:

The application lists the version number in the window top banner. This repo is set up such that the default branch is the most recent version of the program. Please ensure the version you are running on your local machine matches the version listed in the default branch within this repo.

On startup, the application downloads the V2.2 firmware binary file "microSWIFT_V2.2.elf" to the local "firmware" folder to ensure the most recent copy of firmware is burned to the device. If the application is unable to download this file (network issue, etc.), an error will appear indicating so. If this is to occur, users must ensure the firmware folder contains the most recent copy of "microSWIFT_V2.2.elf", which can be downloaded from [the microSWIFT binaries repo](https://github.com/SASlabgroup/microSWIFT-V2-Binaries/tree/main) under the V2.2 folder. 

To bypass the firmware update functionality, pass the flag "--no_firmware_update":
```shell
python microSWIFT_programmer.py --no_firmware_update
```

When downloading a configuration file, no default file extension is applied. If holding for reference, save as ".bin" extansion. If using to conduct over-the-air configuration update, save as ".sbd" extension and ensure the file length with extension does not exceed 80 characters (ex: "microSWIFT_100_configuration.sbd").