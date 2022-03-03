# CloneHeroHero - Clone Hero AI

import numpy as np
import time
import cv2
from mss import mss
from pyKey import pressKey, releaseKey, press, sendSequence, showKeys
from screencap import ScreenCapture


# FIXME - for the defaults, it would be best to save them to a file, and allow program to either load the defaults
#  from the file and start running, or do the setup phase first (saving to file)

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

STRUMS_PER_SECOND = 6
STRUM_DELAY_NS = 1 / STRUMS_PER_SECOND * 1e9

AREA_THRESH = 100

callback_img = None

boundbox_coords = [(534, 490), (1388, 1076)]  # default fixme


def sbb_mouse_callback(event, x, y, flags, param):
    # EVENT_LBUTTONDBLCLK - left double click
    # EVENT_LBUTTONDOWN - left mouse press
    # EVENT_LBUTTONUP - left mouse release
    if event == cv2.EVENT_LBUTTONUP:
        print("x: {}, y: {}".format(x * PREVIEW_SCALE_FACTOR, y * PREVIEW_SCALE_FACTOR))
        boundbox_coords.append((x * PREVIEW_SCALE_FACTOR, y * PREVIEW_SCALE_FACTOR))



bb_left_offset = None
bb_top_offset = None
bb_height = None
bb_width = None

boundbox = {'left': 534, 'top': 490, 'width': 854, 'height': 586}  # default



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


hsv_lowers = np.uint8([  # default
    [55, 100, 100],   # green
    [0, 100, 100],    # red
    [25, 100, 100],   # yellow
    [100, 100, 100],  # blue
    [10, 100, 100]    # orange
])
hsv_uppers = np.uint8([  # default
    [65, 255, 255],
    [5, 255, 255],
    [35, 255, 255],
    [110, 255, 255],
    [20, 255, 255]
])
hsv_setter_idx = 0


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


# perspective corners with respect to the 0, 0 of the bounding box
perspective_corners = [[559, 2], [293, 2], [3, 580], [848, 577]] # fixme


# MAKE SURE TO CLICK CORNERS IN MATHEMATICAL FASHION - QI, QII, QIII, QIV in that order (tr, tl, br, bl)
def perspective_mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONUP:
        perspective_corners.append((x, y))


scene_points = np.float32([  # default
    [559, 2],
    [293, 2],
    [3, 580],
    [848, 577],
])
M = None

warp_width = 600
warp_height = 800


def init_perspective_box():
    global scene_points
    global M
    scene_points = np.float32(perspective_corners)
    target_points = np.float32([[warp_width - 1, 0], [0, 0], [0, warp_height - 1], [warp_width - 1, warp_height - 1]])
    M = cv2.getPerspectiveTransform(scene_points, target_points)


def divide_boundbox(mss_base):
    global callback_img
    # set perspective corners
    callback_img = cv2.imread("boundbox.png") # fixme - make sure this is saved in first steps
    cv2.imshow("screenshot", callback_img)
    cv2.setMouseCallback("screenshot", perspective_mouse_callback)
    _ = cv2.waitKey()
    init_perspective_box()

    # display perspective warp
    warped = cv2.warpPerspective(callback_img, M, dsize=(warp_width, warp_height))
    cv2.imshow("screenshot", warped)
    _ = cv2.waitKey()

    # set colors
    callback_img = cv2.imread("screenshots/boundbox_example.png") # fixme - somehow get screenshot of actual fretboard
    cv2.imshow("screenshot", callback_img)
    cv2.setMouseCallback("screenshot", color_mouse_callback)

    hsv_img = cv2.cvtColor(callback_img, cv2.COLOR_BGR2HSV)
    _ = cv2.waitKey()

    for i in range(5):
        mask = cv2.inRange(hsv_img, hsv_lowers[i], hsv_uppers[i])  # red mask
        cv2.imshow("screenshot", mask)
        _ = cv2.waitKey()


strum_counter = 0


def strum(note_list):
    global last_strum
    global strum_counter
    if False: # fixme
        for note in note_list:
            # print(cidx2key[note])
            pressKey(cidx2key[note])
        if len(note_list) > 0:
            press(STRUM_KEY)
            print("strum", strum_counter)
            strum_counter += 1
        for note in note_list:
            # pass
            releaseKey(cidx2key[note])
        last_strum = current_ns


old_bottom_y = 0


# divide board into 5 columns (green, red, yellow, blue, orange)
def track_columns(old_frame, frame):
    global old_bottom_y
    # FIXME - FOR SPEED - change this to only mask the new frame each iteration rather than both old and new frames.
    #  Could reduce the masking needed by half. Need to figure out how to store the old masks

    col_width = frame.shape[1] / 5  # keep as float

    # todo convert to for loop, passing each column into a method (or try to vectorize)
    col0 = frame[:, int(0*col_width):int(1*col_width), :]
    col1 = frame[:, int(1*col_width):int(2*col_width), :]
    col2 = frame[:, int(2*col_width):int(3*col_width), :]
    col3 = frame[:, int(3*col_width):int(4*col_width), :]
    col4 = frame[:, int(4*col_width):int(5*col_width), :]

    mask0 = cv2.inRange(frame[:, int(0*col_width):int(1*col_width), :], hsv_lowers[0], hsv_uppers[0])
    old_mask0 = cv2.inRange(old_frame[:, int(0*col_width):int(1*col_width), :], hsv_lowers[0], hsv_uppers[0])

    # todo possibly erode and dilate here

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask0)

    mask0_copy = mask0.copy()
    new_bottom_y = 0
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] > AREA_THRESH:
            # centroid: [x, y]
            if centroids[i][1] > new_bottom_y:
                new_bottom_y = centroids[i][1]
            cv2.circle(mask0_copy, (int(centroids[i][0]), int(centroids[i][1])), 35, [125, 125, 125], thickness=7)

    if old_bottom_y > new_bottom_y:
        # note has crossed section, emit signal
        print("Note has crossed", old_bottom_y) # todo emit signal

    old_bottom_y = new_bottom_y
    cv2.imshow("test", mask0_copy)
    _ = cv2.waitKey(1)


old_fret_board = None


def loop_boundbox_feed(mss_base):
    global old_fret_board
    screenshot = np.array(mss_base.grab(boundbox))
    warped = cv2.warpPerspective(screenshot, M, (warp_width, warp_height))
    old_fret_board = cv2.cvtColor(warped, cv2.COLOR_BGR2HSV)  # convert to hsv
    while True:
        screenshot = np.array(mss_base.grab(boundbox))
        warped = cv2.warpPerspective(screenshot, M, (warp_width, warp_height))
        fret_board = cv2.cvtColor(warped, cv2.COLOR_BGR2HSV)

        track_columns(old_fret_board, fret_board)

        old_fret_board = fret_board
        # strum(notes)
        # cv2.imshow("mask", full_mask)
        cv2.imshow("screenshot", fret_board)

        if cv2.waitKey(MS_DELAY) == ord('q'):
            print("quit.")
            cv2.destroyAllWindows()
            break


def main():
    with mss() as sct:
        sc = ScreenCapture(sct, MONITOR)
    #init_properties()
    # set_boundbox(sct)
    # save_bounded_img(sct)

    # divide_boundbox(sct)

    # init_perspective_box()
    # loop_boundbox_feed(sct)

    return


if __name__ == "__main__":
    main()
