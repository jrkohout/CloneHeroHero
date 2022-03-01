# CloneHeroHero - Clone Hero AI

import numpy as np
import time
import cv2
from mss import mss
from PIL import Image

boundbox_coords = list()
boundbox = None

callback_img = None

bb_left_offset = None
bb_top_offset = None
bb_height = None
bb_width = None

def sbb_mouse_callback(event, x, y, flags, param):
    # EVENT_LBUTTONDBLCLK - left double click
    # EVENT_LBUTTONDOWN - left mouse press
    # EVENT_LBUTTONUP - left mouse release
    if event == cv2.EVENT_LBUTTONUP:
        print("x: {}, y: {}".format(x, y))
        boundbox_coords.append((x, y))


def set_boundbox(mss_base):
    print("Available Monitors:")
    for mon in mss_base.monitors:
        print(mon)
    mon = mss_base.monitors[1]  # 1 should be main monitor
    screenshot = mss_base.grab(mon)
    cv2.imshow("screenshot", np.array(screenshot))
    cv2.setMouseCallback("screenshot", sbb_mouse_callback)
    while cv2.waitKey() != ord('q'):
        pass  # TODO - maybe limit to only be able to click twice somehow
    set_offsets()
    global boundbox
    boundbox = {
        'left': bb_left_offset,
        'top': bb_top_offset,
        'width': bb_width,
        'height': bb_height
    }


def set_offsets():
    global bb_left_offset
    global bb_top_offset
    global bb_width
    global bb_height
    bb_coords = np.array(boundbox_coords, dtype=np.int32)
    bb_left_offset = int(np.min(bb_coords[:, 0]))
    bb_top_offset = int(np.min(bb_coords[:, 1]))
    bb_width = int(np.max(bb_coords[:, 0])) - bb_left_offset
    bb_height = int(np.max(bb_coords[:, 1])) - bb_top_offset


def save_bounded_img(mss_base):
    print("bounding box:", boundbox)
    # print("dtype", mon["left"].dtype)
    screenshot = mss_base.grab(boundbox)
    cv2.imshow("screenshot", np.array(screenshot))
    _ = cv2.waitKey()
    cv2.imwrite("boundbox.png", np.array(screenshot))


def color_mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONUP:
        print("x: {}, y: {}".format(x, y))
        print("BGR:", callback_img[y, x, :])


def divide_boundbox(mss_base):
    global callback_img
    callback_img = cv2.imread("screenshots/boundbox_example.png")
    cv2.imshow("screenshot", callback_img)
    cv2.setMouseCallback("screenshot", color_mouse_callback)

    _ = cv2.waitKey()
    hsv_img = cv2.cvtColor(callback_img, cv2.COLOR_BGR2HSV)

    bgr_red = np.uint8([[[0, 0, 154]]])
    hsv_red = cv2.cvtColor(bgr_red, cv2.COLOR_BGR2HSV)  # TODO - left off here
    lower = hsv_red - np.array([[[10, 0, 0]]])
    upper = hsv_red + np.array([[[10, 0, 0]]])

    mask = cv2.inRange(hsv_img, lower, upper)
    cv2.imshow("screenshot", mask)
    _ = cv2.waitKey()





def main():
    print(cv2.version)
    with mss() as sct:
        # set_boundbox(sct)
        # save_bounded_img(sct)
        divide_boundbox(sct)

    return


if __name__ == "__main__":
    main()
