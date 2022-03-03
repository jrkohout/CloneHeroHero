# CloneHeroHero - Clone Hero AI

import numpy as np
import time
import cv2
from mss import mss
from pyKey import pressKey, releaseKey, press, sendSequence, showKeys

from colorcap import ColorCapture
from screenfeed import ScreenFeed


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

def _get_bottom_y(mask):
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)

    mask_copy = mask.copy()
    new_bottom_y = 0
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] > AREA_THRESH:
            # centroid: [x, y]
            if centroids[i][1] > new_bottom_y:
                new_bottom_y = centroids[i][1]
            cv2.circle(mask_copy, np.round(centroids[i]).astype(int), 35, [180, 180, 180], thickness=7) # (int(centroids[i][0]), int(centroids[i][1]))
    return new_bottom_y, mask_copy


class Hero:
    def __init__(self):
        with mss() as sct:
            self._s_feed = ScreenFeed(sct, MONITOR)
        self._c_cap = ColorCapture()
        self._old_bottom_y = np.zeros(5)  # green, red, yellow, blue, orange

    # col0 = frame[:, int(0 * col_width):int(1 * col_width), :]
    # col1 = frame[:, int(1 * col_width):int(2 * col_width), :]
    # col2 = frame[:, int(2 * col_width):int(3 * col_width), :]
    # col3 = frame[:, int(3 * col_width):int(4 * col_width), :]
    # col4 = frame[:, int(4 * col_width):int(5 * col_width), :]

    def play_loop(self):
        new_bottom_y = np.zeros(5)
        while True:
            frame = self._s_feed.next_frame()
            col_width = frame.shape[1] / 5  # keep as float

            # divide board into 5 columns (green, red, yellow, blue, orange)
            # todo try to vectorize this, maybe keeping cols as a numpy array or indices of one
            cols = list()
            for i in range(5):
                cols.append(frame[:, int(i * col_width):int((i+1) * col_width), :])

            cmasks = list()  # todo probably don't want to store these, just using this to display masks for development
            for i in range(5):
                mask = self._c_cap.mask(cols[i], i)
                new_bottom_y[i], circled_mask = _get_bottom_y(mask)
                cmasks.append(circled_mask)

            notes = self._old_bottom_y > new_bottom_y  # true values mean play the note, false values mean don't play it
            if np.any(notes):
                print("Some note has crossed (", notes, ")")  # todo emit signal

            self._old_bottom_y = new_bottom_y

            # strum(notes) todo

            # todo TEMPORARY: DEVELOPMENT
            for i in range(5):
                cv2.imshow("column_{}".format(i), cmasks[i])
                cv2.resizeWindow("column_{}".format(i), 200, 800)

            # cv2.imshow("feed", frame)  # live perspective-warped feed

            if cv2.waitKey(MS_DELAY) == ord('q'):
                print("quit.")
                cv2.destroyAllWindows()
                break


def main():
    hero = Hero()
    hero.play_loop()


if __name__ == "__main__":
    main()
