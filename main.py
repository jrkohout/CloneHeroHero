# CloneHeroHero - Clone Hero AI

import numpy as np
import time
import cv2
from mss import mss
from PIL import Image
from pyKey import pressKey, releaseKey, press, sendSequence, showKeys


MONITOR = 1  # 1 should be main monitor

PREVIEW_SCALE_FACTOR = 2
TARGET_FPS = 240

MS_DELAY = 1000 // TARGET_FPS

STRUM_KEY = 'DOWN'
cidx2key = {  # todo could probably change this to an array
    0: 'g',  # green
    1: 'f',  # red
    2: 'd',  # yellow
    3: 's',  # blue
    4: 'a'   # orange
}

# no notes => 300,000 - 450,000 ish value for a note
PIXEL_THRESHOLD = 500_000

STRUMS_PER_SECOND = 10
STRUM_DELAY_NS = 1 / STRUMS_PER_SECOND * 1e9

boundbox_coords = [(596, 912), (1334, 996)]
boundbox = {'left': 596, 'top': 912, 'width': 738, 'height': 84}

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
hsv_setter_idx = 0

last_strum = time.perf_counter_ns()


def sbb_mouse_callback(event, x, y, flags, param):
    # EVENT_LBUTTONDBLCLK - left double click
    # EVENT_LBUTTONDOWN - left mouse press
    # EVENT_LBUTTONUP - left mouse release
    if event == cv2.EVENT_LBUTTONUP:
        print("x: {}, y: {}".format(x * PREVIEW_SCALE_FACTOR, y * PREVIEW_SCALE_FACTOR))
        boundbox_coords.append((x * PREVIEW_SCALE_FACTOR, y * PREVIEW_SCALE_FACTOR))


def set_boundbox(mss_base):
    print("Available Monitors:")
    for mon in mss_base.monitors:
        print(mon)
    mon = mss_base.monitors[MONITOR]
    screenshot = np.array(mss_base.grab(mon))
    small_width = screenshot.shape[1] // PREVIEW_SCALE_FACTOR
    small_height = screenshot.shape[0] // PREVIEW_SCALE_FACTOR
    small_screenshot = cv2.resize(screenshot, dsize=(small_width, small_height))
    cv2.imshow("screenshot", small_screenshot)
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
    print("Set boundbox to:", boundbox)


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


def get_notes(fret_box):
    global last_strum
    fret_box_hsv = cv2.cvtColor(fret_box, cv2.COLOR_BGR2HSV)
    full_mask = np.zeros(fret_box.shape[:2])
    notes = []
    for idx, (lower, upper) in enumerate(zip(hsv_lowers, hsv_uppers)):
        # mask to index color
        mask = cv2.inRange(fret_box_hsv, lower, upper)
        full_mask += mask
        pixel_sum = mask.sum()
        # print("sum", idx, ':', pixel_sum)
        current_ns = time.perf_counter_ns()
        if current_ns - last_strum > STRUM_DELAY_NS and pixel_sum > PIXEL_THRESHOLD:
            # TODO - finaggle with the delay stuff
            #  also, every time a note is hit, orange sparks are let off, which triggers the orange note to play.
            #  need to maybe make special case for orange, or tighten threshold
            #  or make a better way of strumming notes that isn't just if the segmented pixels have a greater sum than some threshold - try to get position info?
            notes.append(idx)
            last_strum = current_ns
    return notes, full_mask


def strum(note_list):
    for note in note_list:
        # print(cidx2key[note])
        pressKey(cidx2key[note])
    if len(note_list) > 0:
        # print("strum")
        press(STRUM_KEY)
    for note in note_list:
        # pass
        releaseKey(cidx2key[note])


def loop_boundbox_feed(mss_base):
    while True:
        screenshot = np.array(mss_base.grab(boundbox))
        notes, full_mask = get_notes(screenshot)
        strum(notes)
        cv2.imshow("mask", full_mask)
        cv2.imshow("screenshot", screenshot)

        if cv2.waitKey(MS_DELAY) == ord('q'):
            print("quit.")
            cv2.destroyAllWindows()
            break


def main():
    print(cv2.version)
    with mss() as sct:
        # set_boundbox(sct)
        # save_bounded_img(sct)
        # divide_boundbox(sct)
        loop_boundbox_feed(sct)

    return

# for i in range(5):
#     time.sleep(1)
#     press('UP')


if __name__ == "__main__":
    main()
