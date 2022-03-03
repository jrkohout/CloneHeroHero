# screenfeed.py - contains class that initializes and streams a portion of a user's screen

import numpy as np
import cv2
from mss.base import MSSBase
import configparser


PROPERTIES_PATH = "properties.ini"
MONITOR_PREVIEW_SHRINK_FACTOR = 2
WIDTH_STRETCH = 0.75
HEIGHT_STRETCH = 1.5
WARPBOX_PREVIEW_FPS = 30

fretboard_coords = list()


def sbb_mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        fretboard_coords.append((x * MONITOR_PREVIEW_SHRINK_FACTOR, y * MONITOR_PREVIEW_SHRINK_FACTOR))
        print("Point set")


class ScreenFeed:
    def __init__(self, mss: MSSBase, mon_num):
        self._mss = mss
        self._mon_num = mon_num
        print("Available Monitors:")
        for mon in self._mss.monitors:
            print(mon)
        print()
        response = ""
        while response.lower() not in ('y', 'n'):
            response = input("Use screen capture properties from file? (y/n) ")
        if response.lower() == 'y':
            self._load_properties()
        else:
            self._set_properties()
        self._show_preview()


    def _load_properties(self):
        with open(PROPERTIES_PATH) as file:
            config = configparser.ConfigParser()
            config.read(PROPERTIES_PATH)
            # config[section][key]
            fb_corners = config["fretboard_corners"]
            tr = np.array([int(fb_corners["tr_x"]), int(fb_corners["tr_y"])])
            tl = np.array([int(fb_corners["tl_x"]), int(fb_corners["tl_y"])])
            bl = np.array([int(fb_corners["bl_x"]), int(fb_corners["bl_y"])])
            br = np.array([int(fb_corners["br_x"]), int(fb_corners["br_y"])])
            self._boundbox = dict()
            for key in config["bounding_box"]:
                self._boundbox[key] = int(config["bounding_box"][key])
            self._set_warping(tr, tl, bl, br)

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
        small_width = screenshot.shape[1] // MONITOR_PREVIEW_SHRINK_FACTOR
        small_height = screenshot.shape[0] // MONITOR_PREVIEW_SHRINK_FACTOR
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
        cv2.destroyWindow("screenshot")
        fb_coords = np.array(fretboard_coords, dtype=int)
        # top right and top left will have x values of the highest two points
        # top y points share the smallest y
        top_two = fb_coords[np.argsort(fb_coords[:, 1])[:2]]
        top_two_sorted = top_two[np.argsort(top_two[:, 0])]
        min_y = np.min(fb_coords[:, 1])
        tr = np.array([top_two_sorted[1, 0], min_y])
        tl = np.array([top_two_sorted[0, 0], min_y])
        # bottom y points share the largest y
        # bottom left x is smallest x, bottom right x is largest x
        max_y = np.max(fb_coords[:, 1])
        bl = np.array([np.min(fb_coords[:, 0]), max_y])
        br = np.array([np.max(fb_coords[:, 0]), max_y])

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

        self._set_warping(tr, tl, bl, br)
        # TODO - break this into smaller methods
        return fretboard_corners

    def _set_warping(self, tr, tl, bl, br):
        self._warp_width = self._boundbox["width"] * WIDTH_STRETCH
        self._warp_height = self._boundbox["height"] * HEIGHT_STRETCH
        scene_points = np.float32([
            [tr[0] - self._boundbox["left"], 0],
            [tl[0] - self._boundbox["left"], 0],
            [0, bl[1] - self._boundbox["top"]],
            [br[0] - self._boundbox["left"], bl[1] - self._boundbox["top"]]
        ])
        target_points = np.float32([
            [int(self._warp_width - 1), 0],
            [0, 0],
            [0, int(self._warp_height - 1)],
            [int(self._warp_width - 1), int(self._warp_height - 1)]
        ])
        self._M = cv2.getPerspectiveTransform(scene_points, target_points)

    def _show_preview(self):
        print("Showing preview. Press 'q' to continue.")
        preview_ms_delay = 1000 // WARPBOX_PREVIEW_FPS
        while cv2.waitKey(preview_ms_delay) != ord('q'):
            screenshot = np.array(self._mss.grab(self._boundbox))
            warped = cv2.warpPerspective(screenshot, self._M, dsize=(int(self._warp_width), int(self._warp_height)))
            cv2.imshow("screenshot", screenshot)
            cv2.imshow("warped", warped)
        cv2.destroyAllWindows()
