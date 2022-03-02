# screencap.py - contains class that initializes and streams a portion of a user's screen
import numpy as np
import cv2
from mss.base import MSSBase
import configparser


PROPERTIES_PATH = "properties.ini"
PREVIEW_SCALE_FACTOR = 2
WARP_WIDTH = 600
WARP_HEIGHT = 800

fretboard_coords = list()


def sbb_mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        fretboard_coords.append((x * PREVIEW_SCALE_FACTOR, y * PREVIEW_SCALE_FACTOR))


class ScreenCapture:
    def __init__(self, mss: MSSBase, mon_num):
        self._mss = mss
        self._mon_num = mon_num
        print("Available Monitors:")
        for mon in self._mss.monitors:
            print(mon)
        print()
        response = ""
        while response.lower() not in ('y', 'n'):
            response = input("Use properties from file? (y/n) ")
        if response.lower() == 'y':
            self._load_properties()
        else:
            self._set_properties()

    def _load_properties(self):
        with open(PROPERTIES_PATH) as file:
            pass # TODO

    def _set_properties(self):
        config = configparser.ConfigParser()

        self._set_bounding_box()

        bb_s2s = {}
        for key in self._boundbox.keys():
            bb_s2s[key] = str(self._boundbox[key])
        config["bounding_box"] = bb_s2s

        with open(PROPERTIES_PATH, 'w') as configfile:
            config.write(configfile)


    def _set_bounding_box(self):
        mon = self._mss.monitors[self._mon_num]
        screenshot = np.array(self._mss.grab(mon))
        small_width = screenshot.shape[1] // PREVIEW_SCALE_FACTOR
        small_height = screenshot.shape[0] // PREVIEW_SCALE_FACTOR
        small_screenshot = cv2.resize(screenshot, dsize=(small_width, small_height))
        cv2.imshow("screenshot", small_screenshot)
        cv2.setMouseCallback("screenshot", sbb_mouse_callback)
        keep_looping = True
        while keep_looping:
            keep_looping = cv2.waitKey() != ord('q')
            if not keep_looping and len(fretboard_coords) < 4:
                print("Please click all four corners of fret board.")
                keep_looping = False

        fb_coords = np.array(fretboard_coords, dtype=np.int32)
        top_two = np.argsort(fb_coords[:, 1])[:2]
        # FIXME - URGENT: this is wrong. Need to calculate top right as highest y with highest x, tl as highest y with lowest x
        tr = (int(fb_coords[top_two[0]][0]), int(fb_coords[top_two[0]][1]))
        tl = (int(fb_coords[top_two[1]][0]), int(fb_coords[top_two[1]][1]))
        bl = (int(np.min(fb_coords[:, 0])), int(np.max(fb_coords[:, 1])))
        br = (int(np.max(fb_coords[:, 0])), int(np.max(fb_coords[:, 1])))

        scene_points = np.float32([tr, tl, br, bl])
        target_points = np.float32(
            [[WARP_WIDTH - 1, 0],
             [0, 0],
             [0, WARP_HEIGHT - 1],
             [WARP_WIDTH - 1, WARP_HEIGHT - 1]]
        )
        self._M = cv2.getPerspectiveTransform(scene_points, target_points)
        # TODO - store tr, tl, bl, br as properties - left off here

        print("DEBUG - tr:{}, tl:{}, bl:{}, br:{}", tr, tl, bl, br)

        bb_left = bl[0]
        bb_top = min(tl[1], tr[1])
        bb_width = br[0] - bb_left
        bb_height = max(bl[1], br[1]) - bb_top

        self._boundbox = {
            "left": bb_left,
            "top": bb_top,
            "width": bb_width,
            "height": bb_height
        }
        print("DEBUG: Set boundbox to:", self._boundbox)
        # TODO - break this into smaller methods
