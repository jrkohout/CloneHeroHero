# CloneHeroHero - Clone Hero AI

import numpy as np
import time
import cv2
from mss import mss
from PIL import Image

boundbox_coords = list()
boundbox = None  # TODO - create default boundbox so that we can skip corner selection at the beginning

callback_img = None

bb_left_offset = None
bb_top_offset = None
bb_height = None
bb_width = None

hsv_lowers = np.uint8([
    [55, 100, 100],   # green
    [0, 100, 100],    # red
    [25, 100, 100],   # yellow
    [100, 100, 100],  # blue
    [10, 100, 100]    # orange
])
hsv_uppers = np.uint8([
    [65, 255, 255],
    [5, 255, 255],
    [35, 255, 255],
    [110, 255, 255],
    [20, 255, 255]
])
# 1 - hsv_red
# 2 - hsv_yellow
# 3 - hsv_blue
# 4 - hsv_orange
hsv_setter_idx = 0



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
    global hsv_lowers
    global hsv_uppers
    global hsv_setter_idx
    if event == cv2.EVENT_LBUTTONUP:
        print("x: {}, y: {}".format(x, y))
        # bgr - [0-255, 0-255, 0-255]
        # hsv - [0-179, 0-255, 0-255]
        bgr = callback_img[y, x, :]
        hsv = cv2.cvtColor(callback_img[y, x, :].reshape((1, 1, 3)), cv2.COLOR_BGR2HSV)
        print("BGR:", bgr)
        print("HSV:", hsv)
        if hsv_setter_idx < 5:
            hsv_lowers[hsv_setter_idx] = np.uint8([max(hsv[0, 0, 0] - 5, 0), 100, 100])  # TODO - adjust blue maybe
            hsv_uppers[hsv_setter_idx] = np.uint8([min(hsv[0, 0, 0] + 5, 179), 255, 255])
            print("set color ranges for", hsv_setter_idx)
            hsv_setter_idx += 1


def divide_boundbox(mss_base):
    global callback_img
    callback_img = cv2.imread("screenshots/boundbox_example.png")
    cv2.imshow("screenshot", callback_img)
    cv2.setMouseCallback("screenshot", color_mouse_callback)

    hsv_img = cv2.cvtColor(callback_img, cv2.COLOR_BGR2HSV)
    _ = cv2.waitKey()

    for i in range(5):
        mask = cv2.inRange(hsv_img, hsv_lowers[i], hsv_uppers[i])  # red mask
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
