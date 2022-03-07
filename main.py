# CloneHeroHero - Clone Hero AI

import numpy as np
import cv2
from mss import mss

from colorcap import ColorCapture
from guitar import Guitar, release_all
from screenfeed import ScreenFeed

import settings


class Hero:
    def __init__(self, do_previews, load_sf_properties, load_cc_properties):
        with mss() as sct:
            self._s_feed = ScreenFeed(sct, settings.MONITOR, do_previews, load_sf_properties)
        self._c_cap = ColorCapture(do_previews, load_cc_properties)
        self._old_bottom_y = np.zeros(5)  # green, red, yellow, blue, orange
        self._guitar = Guitar()

    # TODO - try doing connectedcomponents on the whole frame rather than column by column?
    # TODO - I wonder if I can use some logic to better detect multi-note strums, the bot sometimes struggles with those
    def _get_bottom_y(self, mask_columns, new_bottom_y):
        for i, mask_col in enumerate(mask_columns):
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask_col)
            col_bottom_y = 0
            for j in range(1, num_labels):
                # consider centroid if the area of the blob is great enough, but ignore if the width is too small
                # (too small width => note tail)
                if stats[j, cv2.CC_STAT_AREA] > settings.AREA_THRESH:
                    if stats[j, cv2.CC_STAT_WIDTH] > settings.NOTE_TAIL_WIDTH_THRESH:
                        # likely a note
                        # centroid: [x, y]
                        if centroids[j][1] > col_bottom_y:
                            col_bottom_y = centroids[j][1]
                        if settings.SHOW_FEED and settings.DEV_MODE:
                            cv2.circle(mask_col, np.round(centroids[j]).astype(int), 10, [124, 124, 124], thickness=10)
                    # else: TODO - figure out better way of dealing with tails here
                        # likely a tail
                        # do something with col_bottom_tail_y
                        # pass
            new_bottom_y[i] = col_bottom_y

            self._guitar.check_strum()  # FIXME check strum

    def play_loop(self):
        frame = np.empty(self._s_feed.frame_shape, dtype=np.uint8)
        frame_columns = np.array_split(frame, 5, axis=1)  # produces evenly spaced column views into frame
        mask = np.empty(self._s_feed.frame_shape[:2], dtype=np.uint8)
        mask_columns = np.array_split(mask, 5, axis=1)  # produces evenly spaced column views into mask
        new_bottom_y = np.zeros(5)

        while True:
            # TODO - adding all those checks (the FIXME check strum checks) seems to work really well on a good PC, should try to better incorporate them
            self._s_feed.put_next_frame(frame)
            # divide board into 5 columns (green, red, yellow, blue, orange)

            self._guitar.check_strum()  # FIXME check strum

            for i in range(len(frame_columns)):  # TODO - could maybe hard code each different column here rather than a for loop
                # TODO - once in a while, it appears that some notes are not picked up by segmentation or are split into
                #  two small parts that are ignored for being too small - further investigation required (record video
                #  of both bot view and game view and see what the errors look like)
                self._c_cap.mask(frame_columns[i], i, mask_columns[i])
                self._guitar.check_strum()  # FIXME check strums

            # TODO - try implementing support for open strums (pick purple color and segment the whole frame, or a
            #  narrow band of the frame since it's pretty skinny)

            self._get_bottom_y(mask_columns, new_bottom_y)

            notes = self._old_bottom_y > new_bottom_y  # true values mean play the note, false values mean don't play it

            if np.any(notes):
                self._guitar.enqueue_strum(notes)

            self._guitar.check_strum()  # FIXME check strum

            np.copyto(self._old_bottom_y, new_bottom_y)

            if settings.SHOW_FEED:
                cv2.imshow("mask_feed", mask)

            self._guitar.check_strum()  # FIXME check strum

            k = cv2.waitKey(settings.MS_DELAY)  # TODO - might be able to do 0 or 1 ms delay to speed up?
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


# returns true if yes, false if no
def prompt_yn(prompt):
    response = ""
    while response.lower() not in ('y', 'n'):
        response = input(prompt)
    return response.lower() == 'y'


def main():
    try:
        # TODO - make better prompts, better integrate setup
        do_previews = not prompt_yn("Skip previews of screen feed and color capture? (y/n) ")
        load_sfp = prompt_yn("Load screen feed properties from file? (y/n) ")
        load_ccp = prompt_yn("Load color capture properties from file? (y/n) ")

        hero = Hero(do_previews, load_sfp, load_ccp)
        hero.play_loop()
    finally:
        release_all()


if __name__ == "__main__":
    main()
