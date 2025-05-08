import PyInstaller.__main__

PyInstaller.__main__.run([
    'microSWIFT_programmer.py',
    '--onefile',
    '--windowed',
    '--noconsole',
    '--icon=icon.icns'
])