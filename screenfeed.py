# screenfeed.py - contains class that initializes and streams a portion of a user's screen

import math
import numpy as np
import cv2
from mss.base import MSSBase
import configparser

import settings

fretboard_coords = list()


def calculate_clipped_corners(tr, tl, bl, br):
    # clip off top and bottom of fretboard
    rail_length = ((tl[0] - bl[0]) ** 2 + (bl[1] - tl[1]) ** 2) ** 0.5
    angle = math.atan2(tl[0] - bl[0], bl[1] - tl[1])

    # these are all positive based on how the point-picking is characterized
    # (as long as fretboard looks like this -> / \)
    bottom_y = settings.BOTTOM_SNIP_PROPORTION * rail_length * math.cos(angle)
    bottom_x = settings.BOTTOM_SNIP_PROPORTION * rail_length * math.sin(angle)
    top_y = settings.TOP_SNIP_PROPORTION * rail_length * math.cos(angle)
    top_x = settings.TOP_SNIP_PROPORTION * rail_length * math.sin(angle)

    clipped_tl = np.array([int(tl[0] - top_x), int(tl[1] + top_y)])
    clipped_bl = np.array([int(bl[0] + bottom_x), int(bl[1] - bottom_y)])
    clipped_tr = np.array([int(tr[0] + top_x), int(tr[1] + top_y)])
    clipped_br = np.array([int(br[0] - bottom_x), int(br[1] - bottom_y)])

    return clipped_tr, clipped_tl, clipped_bl, clipped_br


def sbb_mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        fretboard_coords.append(
            (int(x * settings.MONITOR_PREVIEW_SHRINK_FACTOR), int(y * settings.MONITOR_PREVIEW_SHRINK_FACTOR))
        )
        print("Point set - ({}, {})".format(x, y))


class ScreenFeed:
    def __init__(self, mss: MSSBase, mon_num, show_preview, load_properties):
        self._mss = mss
        self._mon_num = mon_num
        self._mon = self._mss.monitors[self._mon_num]
        print("Available Monitors:")
        for mon in self._mss.monitors:
            print(mon)
        print()
        if load_properties:
            self._load_properties()
        else:
            self._set_properties()
        if show_preview:
            self._show_preview()

    def _load_properties(self):
        config = configparser.ConfigParser()
        config.read(settings.PROPERTIES_PATH)
        # config[section][key]
        fb_corners = config["fretboard_corners"]
        tr = np.array([int(fb_corners["tr_x"]), int(fb_corners["tr_y"])])
        tl = np.array([int(fb_corners["tl_x"]), int(fb_corners["tl_y"])])
        bl = np.array([int(fb_corners["bl_x"]), int(fb_corners["bl_y"])])
        br = np.array([int(fb_corners["br_x"]), int(fb_corners["br_y"])])
        clipped_tr, clipped_tl, clipped_bl, clipped_br = calculate_clipped_corners(tr, tl, bl, br)
        self._set_boundbox(clipped_tr, clipped_tl, clipped_bl, clipped_br)
        self._set_warping(clipped_tr, clipped_tl, clipped_bl, clipped_br)

    def _set_properties(self):
        config = configparser.ConfigParser()
        config["fretboard_corners"] = self._set_capture_bounds()
        with open(settings.PROPERTIES_PATH, 'w') as configfile:
            config.write(configfile)

    def _set_capture_bounds(self):  # todo - break apart this method; make what it is doing clearer
        screenshot = np.array(self._mss.grab(self._mon))
        small_width = int(screenshot.shape[1] / settings.MONITOR_PREVIEW_SHRINK_FACTOR)
        small_height = int(screenshot.shape[0] / settings.MONITOR_PREVIEW_SHRINK_FACTOR)
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

        fretboard_corners = {  # in relation to the opencv window (in relation to top left corner of the given monitor)
            "tr_x": str(tr[0]),
            "tr_y": str(tr[1]),
            "tl_x": str(tl[0]),
            "tl_y": str(tl[1]),
            "bl_x": str(bl[0]),
            "bl_y": str(bl[1]),
            "br_x": str(br[0]),
            "br_y": str(br[1]),
        }

        # these are again in relation to top left corner of the given monitor
        clipped_tr, clipped_tl, clipped_bl, clipped_br = calculate_clipped_corners(tr, tl, bl, br)
        self._set_boundbox(clipped_tr, clipped_tl, clipped_bl, clipped_br)
        self._set_warping(clipped_tr, clipped_tl, clipped_bl, clipped_br)
        return fretboard_corners

    def _set_boundbox(self, tr, tl, bl, br):
        bb_left = self._mon["left"] + bl[0]
        bb_top = self._mon["top"] + min(tl[1], tr[1])
        bb_width = br[0] - bl[0]
        bb_height = max(bl[1], br[1]) - min(tl[1], tr[1])
        self._boundbox = {
            "left": int(bb_left),
            "top": int(bb_top),
            "width": int(bb_width),
            "height": int(bb_height),
            "mon": self._mon_num
        }

    def _set_warping(self, tr, tl, bl, br):
        self._warp_width = self._boundbox["width"] * settings.WIDTH_STRETCH
        self._warp_height = self._boundbox["height"] * settings.HEIGHT_STRETCH

        bb_left_translated = abs(self._mon["left"] - self._boundbox["left"])

        scene_points = np.float32([
            [tr[0] - bb_left_translated, 0],
            [tl[0] - bb_left_translated, 0],
            [0, self._boundbox["height"]],
            [self._boundbox["width"], self._boundbox["height"]]
        ])
        target_points = np.float32([
            [int(self._warp_width), 0],
            [0, 0],
            [0, int(self._warp_height)],
            [int(self._warp_width), int(self._warp_height)]
        ])
        self._M = cv2.getPerspectiveTransform(scene_points, target_points)

    def _show_preview(self):
        print("Showing preview. Press 'q' to continue.")
        preview_ms_delay = 1000 // settings.WARPBOX_PREVIEW_FPS
        while cv2.waitKey(preview_ms_delay) != ord('q'):
            screenshot = np.array(self._mss.grab(self._boundbox))
            warped = cv2.warpPerspective(screenshot, self._M, dsize=(int(self._warp_width), int(self._warp_height)))
            cv2.imshow("screenshot", screenshot)
            cv2.imshow("warped", warped)
        cv2.destroyAllWindows()

    def put_next_frame(self, dest_arr):
        cv2.warpPerspective(
            cv2.cvtColor(  # convert to hsv
                np.array(self._mss.grab(self._boundbox), dtype=np.uint8),  # need to use float32 for OpenCV
                cv2.COLOR_BGR2HSV
            ),
            self._M,
            dsize=(int(self._warp_width), int(self._warp_height)),
            dst=dest_arr
        )

    @property
    def frame_shape(self):
        return self._warp_height, self._warp_width, 3  # height x width x channels (HSV)
