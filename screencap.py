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
        print("Point set")


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
        self._show_preview()

    def _load_properties(self):
        with open(PROPERTIES_PATH) as file:
            pass # TODO

    def _set_properties(self):
        config = configparser.ConfigParser()

        config["fretboard_corners"] = self._set_bounding_box()

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
        print("Click on the four corners of the fret board and press 'q' when finished.")
        keep_looping = True
        while keep_looping:
            if cv2.waitKey() == ord('q'):
                if len(fretboard_coords) < 4:
                    print("Please click on all four corners of fret board.")
                else:
                    keep_looping = False
        fb_coords = np.array(fretboard_coords, dtype=int)
        # top right and top left will have x values of the highest two points
        # top y points share the smallest y
        top_two = fb_coords[np.argsort(fb_coords[:, 1])[:2]]
        print("DEBUG - top two")
        print(top_two)
        top_two_sorted = top_two[np.argsort(top_two[:, 0])]
        print("DEBUG - top two sorted")
        print(top_two_sorted)
        min_y = np.min(fb_coords[:, 1])
        tr = np.array([top_two_sorted[1, 0], min_y])
        tl = np.array([top_two_sorted[0, 0], min_y])
        # bottom y points share the largest y
        # bottom left x is smallest x, bottom right x is largest x
        max_y = np.max(fb_coords[:, 1])
        bl = np.array([np.min(fb_coords[:, 0]), max_y])
        br = np.array([np.max(fb_coords[:, 0]), max_y])
        # todo - might need to cast these to integers

        scene_points = np.float32([tr, tl, br, bl])
        target_points = np.float32(
            [[WARP_WIDTH - 1, 0],
             [0, 0],
             [0, WARP_HEIGHT - 1],
             [WARP_WIDTH - 1, WARP_HEIGHT - 1]]
        )
        self._M = cv2.getPerspectiveTransform(scene_points, target_points)
        # TODO - store tr, tl, bl, br as properties - left off here

        fretboard_corners = {
            "tr_x": str(tr[0]),
            "tr_y": str(tr[1]),
            "tl_x": str(tl[0]),
            "tl_y": str(tl[1]),
            "bl_x": str(bl[0]),
            "bl_y": str(bl[1]),
            "br_x": str(br[0]),
            "br_y": str(br[1]),
        }

        print("DEBUG - tr:{}, tl:{}, bl:{}, br:{}".format(tr, tl, bl, br))

        bb_left = bl[0]
        bb_top = min(tl[1], tr[1])
        bb_width = br[0] - bb_left
        bb_height = max(bl[1], br[1]) - bb_top

        self._boundbox = {
            "left": int(bb_left),
            "top": int(bb_top),
            "width": int(bb_width),
            "height": int(bb_height)
        }
        print("DEBUG: Set boundbox to:", self._boundbox)
        # TODO - break this into smaller methods

        return fretboard_corners

    def _show_preview(self):
        screenshot = np.array(self._mss.grab(self._boundbox))
        warped = cv2.warpPerspective(screenshot, self._M, dsize=(WARP_WIDTH, WARP_HEIGHT))

        cv2.imshow("screenshot", screenshot)
        _ = cv2.waitKey()

        cv2.imshow("screenshot", warped)
        print("Press any key to continue.")
        _ = cv2.waitKey()
