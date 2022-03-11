# colorcap.py - contains class that initializes color ranges to mask images

import cv2
import numpy as np

import settings

callback_img = None
# rows: green, red, yellow, blue, orange
hsv_note_colors = np.empty((5, 3), dtype=np.uint8)
hsv_setter_idx = 0


def color_mouse_callback(event, x, y, flags, param):
    global hsv_note_colors
    global hsv_setter_idx
    if event == cv2.EVENT_LBUTTONDOWN:
        # bgr - [0-255, 0-255, 0-255]
        # hsv - [0-179, 0-255, 0-255]
        bgr = callback_img[y, x, :]
        hsv = cv2.cvtColor(callback_img[y, x, :].reshape((1, 1, 3)), cv2.COLOR_BGR2HSV)
        print("BGR:", bgr, "  HSV:", hsv[0, 0, :])
        if hsv_setter_idx < 5:
            hsv_note_colors[hsv_setter_idx] = hsv
            print("Set color for note", hsv_setter_idx)
            hsv_setter_idx += 1


class ColorCapture:
    def __init__(self, show_preview, load_properties):
        if load_properties:
            self._load_colors()
        else:
            self._set_colors()
        if show_preview:
            self._show_color_preview()

    def _load_colors(self):
        with open(settings.COLORS_PATH, 'rb') as file:
            hsv_colors = np.load(file)

        self._set_hsv_bounds(hsv_colors)

    def _set_colors(self):
        global callback_img
        note_img = cv2.imread(settings.NOTES_SCREENSHOT_PATH)
        big_width = note_img.shape[1] * settings.COLOR_PICKING_GROWTH_FACTOR
        big_height = note_img.shape[0] * settings.COLOR_PICKING_GROWTH_FACTOR
        callback_img = cv2.resize(note_img, dsize=(big_width, big_height))
        cv2.imshow("color_selection", callback_img)
        cv2.setMouseCallback("color_selection", color_mouse_callback)
        print("Click on each color in left-to-right order (green, red, yellow, blue, orange). "
              "Press 'q' when finished.")
        keep_looping = True
        while keep_looping:
            if cv2.waitKey() == ord('q'):
                if hsv_setter_idx < 5:
                    print("Please click on all five note colors.")
                else:
                    keep_looping = False
        cv2.destroyWindow("color_selection")

        with open(settings.COLORS_PATH, 'wb') as file:
            np.save(file, hsv_note_colors)

        self._set_hsv_bounds(hsv_note_colors)

    def _set_hsv_bounds(self, hsv_colors):
        # z = np.zeros((5, 1), dtype=np.int16)
        # a = 179 * np.ones((5, 1), dtype=np.int16)
        # hues = hsv_colors[:, 0].reshape(-1, 1).astype(np.int16)
        # low_hues = np.max(np.hstack([hues - settings.HUE_RADIUS, z]), axis=1).reshape(-1, 1).astype(np.uint8)
        # high_hues = np.min(np.hstack([hues + settings.HUE_RADIUS, a]), axis=1).reshape(-1, 1).astype(np.uint8)
        # h = 100 * np.ones((5, 2), dtype=np.uint8)
        # t = 255 * np.ones((5, 2), dtype=np.uint8)
        # self._hsv_lowers = np.hstack([low_hues, h])
        # self._hsv_uppers = np.hstack([high_hues, t])

        # TODO - Temporarily overriding the color bounds; redo the color picking using amalgamation.png and a bunch of
        #  clicks
        # TODO - could keep color picking (and maybe frame bounds selection) as a seperate app

        self._hsv_lowers = np.uint8([
            [55, 100, 100],
            [0, 100, 100],
            [25, 100, 100],
            [95, 100, 100],  # Need to watch out for the blue glowing outlines around star notes
            [15, 100, 100]
        ])
        self._hsv_uppers = np.uint8([
            [65, 255, 255],
            [5, 255, 255],
            [35, 255, 255],
            [110, 255, 255],
            [35, 255, 255]
        ])

    def _show_color_preview(self):
        note_img = cv2.imread(settings.NOTES_SCREENSHOT_PATH)
        hsv_img = cv2.cvtColor(note_img, cv2.COLOR_BGR2HSV)
        for i in range(5):
            print("Viewing mask for color {}. Press any key to continue.".format(i))
            mask = cv2.inRange(hsv_img, self._hsv_lowers[i], self._hsv_uppers[i])
            cv2.imshow("mask_preview", mask)
            _ = cv2.waitKey()
        cv2.destroyWindow("mask_preview")

    def mask(self, img_hsv, color_idx, dest_img):
        cv2.inRange(img_hsv, self._hsv_lowers[color_idx], self._hsv_uppers[color_idx], dst=dest_img)
