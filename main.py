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

# todo maybe remove these? don't want much delay
# STRUMS_PER_SECOND = 6
# STRUM_DELAY_NS = 1 / STRUMS_PER_SECOND * 1e9

AREA_THRESH = 100

strum_counter = 0


# def strum(note_list):
#     global last_strum
#     global strum_counter
#     if False: # fixme
#         for note in note_list:
#             # print(cidx2key[note])
#             pressKey(cidx2key[note])
#         if len(note_list) > 0:
#             press(STRUM_KEY)
#             print("strum", strum_counter)
#             strum_counter += 1
#         for note in note_list:
#             # pass
#             releaseKey(cidx2key[note])
#         last_strum = current_ns

class Hero:
    def __init__(self):
        with mss() as sct:
            self._sc = ScreenCapture(sct, MONITOR)
        self._old_fretboard = None  # TODO start here (design first)
        self._old_bottom_y = None

    # divide board into 5 columns (green, red, yellow, blue, orange)
    def _track_columns(self):
        # FIXME - FOR SPEED - change this to only mask the new frame each iteration rather than both old and new frames.
        #  Could reduce the masking needed by half. Need to figure out how to store the old masks

        col_width = frame.shape[1] / 5  # keep as float

        # todo convert to for loop, passing each column into a method (or try to vectorize)
        col0 = frame[:, int(0 * col_width):int(1 * col_width), :]
        col1 = frame[:, int(1 * col_width):int(2 * col_width), :]
        col2 = frame[:, int(2 * col_width):int(3 * col_width), :]
        col3 = frame[:, int(3 * col_width):int(4 * col_width), :]
        col4 = frame[:, int(4 * col_width):int(5 * col_width), :]

        mask0 = cv2.inRange(frame[:, int(0 * col_width):int(1 * col_width), :], hsv_lowers[0], hsv_uppers[0])
        old_mask0 = cv2.inRange(old_frame[:, int(0 * col_width):int(1 * col_width), :], hsv_lowers[0],
                                hsv_uppers[0])

        # todo possibly erode and dilate here

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask0)

        mask0_copy = mask0.copy()
        new_bottom_y = 0
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] > AREA_THRESH:
                # centroid: [x, y]
                if centroids[i][1] > new_bottom_y:
                    new_bottom_y = centroids[i][1]
                cv2.circle(mask0_copy, (int(centroids[i][0]), int(centroids[i][1])), 35, [125, 125, 125],
                           thickness=7)

        if old_bottom_y > new_bottom_y:
            # note has crossed section, emit signal
            print("Note has crossed", old_bottom_y)  # todo emit signal

        old_bottom_y = new_bottom_y
        cv2.imshow("test", mask0_copy)
        _ = cv2.waitKey(1)

    def play_loop(self):
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
    hero = Hero()
    hero.play_loop()


if __name__ == "__main__":
    main()
