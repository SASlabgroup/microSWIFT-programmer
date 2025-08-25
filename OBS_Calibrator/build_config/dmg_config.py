# DMG configuration for OBS Calibrator

import os.path

# Basic settings
format = 'UDZO'
size = '200M'
files = ['dist/OBS_Calibrator.app']
symlinks = {'Applications': '/Applications'}

# Window settings
window_rect = ((100, 100), (600, 400))
icon_locations = {
    'OBS_Calibrator.app': (150, 200),
    'Applications': (450, 200),
}

# Background and appearance
background = None  # You can add a background image path here
show_status_bar = False
show_tab_view = False
show_toolbar = False
show_pathbar = False
show_sidebar = False
sidebar_width = 180

# Icon settings
icon_size = 100
text_size = 16
