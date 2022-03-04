# CloneHeroHero - Clone Hero AI

import numpy as np
import cv2
from mss import mss

from colorcap import ColorCapture
from guitar import Guitar
from screenfeed import ScreenFeed

import settings


def _get_bottom_y(mask):
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)

    mask_copy = mask.copy()  # TODO - temporary for development
    bottom_y = 0
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] > settings.AREA_THRESH:  # FIXME adjust area threshold
            # centroid: [x, y]
            if centroids[i][1] > bottom_y:
                bottom_y = centroids[i][1]
            cv2.circle(mask_copy, np.round(centroids[i]).astype(int), 35, [180, 180, 180], thickness=7)
    return bottom_y, mask_copy


class Hero:
    def __init__(self, do_previews, load_sf_properties, load_cc_properties):
        with mss() as sct:
            self._s_feed = ScreenFeed(sct, settings.MONITOR, do_previews, load_sf_properties)
        self._c_cap = ColorCapture(do_previews, load_cc_properties)
        self._old_bottom_y = np.zeros(5)  # green, red, yellow, blue, orange
        self._guitar = Guitar()

    def play_loop(self):
        new_bottom_y = np.zeros(5)
        self._guitar.start_thread()
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
                self._guitar.enqueue_strum(notes)

            self._old_bottom_y = new_bottom_y.copy()

            # todo TEMPORARY: DEVELOPMENT
            cv2.imshow("feed", frame)
            for i in range(5):
                cv2.imshow("column_{}".format(i), cmasks[i])
                cv2.resizeWindow("column_{}".format(i), 200, frame.shape[0])

            k = cv2.waitKey(settings.MS_DELAY)
            if k != -1:
                if k == ord('q'):
                    print("quit.")
                    cv2.destroyAllWindows()
                    break
                elif k == ord('w'):
                    settings.STRUM_DELAY_NS += 1e6
                    print("Increased strum delay to", settings.STRUM_DELAY_NS / 1e6, "ms.")
                elif k == ord('s'):
                    settings.STRUM_DELAY_NS -= 1e6
                    print("Decreased strum delay to", settings.STRUM_DELAY_NS / 1e6, "ms.")
        self._guitar.end_thread()


# returns true if yes, false if no
def prompt_yn(prompt):
    response = ""
    while response.lower() not in ('y', 'n'):
        response = input(prompt)
    return response.lower() == 'y'


def main():
    do_previews = not prompt_yn("Skip previews of screen feed and color capture? (y/n) ")
    load_sfp = prompt_yn("Load screen feed properties from file? (y/n) ")
    load_ccp = prompt_yn("Load color capture properties from file? (y/n) ")

    hero = Hero(do_previews, load_sfp, load_ccp)
    hero.play_loop()


if __name__ == "__main__":
    main()
