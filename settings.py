# settings.py - centralized location of all global variables of the project

import numpy

### Main Stuff
MONITOR = 1  # 1 should be main monitor

TARGET_FPS = 240
MS_DELAY = 1000 // TARGET_FPS

AREA_THRESH = 1500  # TODO - adjust

NO_FRET_PROP = 0.4

STRUM_DELAY_MS = 180
STRUM_DELAY_NS = STRUM_DELAY_MS * 1e6

### Keybinds
# in-game keybinds for green, red, yellow, blue, and orange, respectively
NOTE_KEYS = numpy.array(['a', 's', 'j', 'k', 'l'])
#                  |== G == R == Y == B == O ===========*==*==*==*==*=======-----=====|
STRUM_KEY = 'DOWN'

### Perspective Warp Stuff
PROPERTIES_PATH = "properties.ini"
MONITOR_PREVIEW_SHRINK_FACTOR = 2
WIDTH_STRETCH = 0.75
HEIGHT_STRETCH = 1.5
WARPBOX_PREVIEW_FPS = 30

### Color Stuff
NOTES_SCREENSHOT_PATH = "screenshots/note_colors.png"
COLORS_PATH = "hsv_colors.npy"
COLOR_PICKING_GROWTH_FACTOR = 2
HUE_RADIUS = 5
