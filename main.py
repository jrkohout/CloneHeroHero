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
        self._old_note_bottom_y = np.zeros(5, dtype=int)  # green, red, yellow, blue, orange
        self._old_bottom_tail_top_y = np.zeros(5, dtype=int)
        self._old_bottom_tail_bottom_y = np.zeros(5, dtype=int)
        self._guitar = Guitar()

    def _get_note_positions(self, mask_columns, new_note_bottom_y, new_bottom_tail_top_y, new_bottom_tail_bottom_y):
        for i, mask_col in enumerate(mask_columns):
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask_col)

            relevant_stats = stats[1:][stats[1:, cv2.CC_STAT_HEIGHT] > settings.NOTE_HEIGHT_THRESH]
            note_idx = relevant_stats[:, cv2.CC_STAT_WIDTH] > settings.NOTE_TAIL_WIDTH_THRESH

            note_stats = relevant_stats[note_idx]
            tail_stats = relevant_stats[~note_idx]

            new_note_bottom_y[i] = np.max(note_stats[:, cv2.CC_STAT_TOP]) if note_stats.shape[0] > 0 else 0
            new_bottom_tail_top_y[i] = np.max(tail_stats[:, cv2.CC_STAT_TOP]) if tail_stats.shape[0] > 0 else 0
            new_bottom_tail_bottom_y[i] = np.max(tail_stats[:, cv2.CC_STAT_TOP] + tail_stats[:, cv2.CC_STAT_HEIGHT]) \
                if tail_stats.shape[0] > 0 else 0

            if settings.SHOW_FEED and settings.DEV_MODE:
                if new_note_bottom_y[i] != 0:
                    cv2.line(mask_col, (0, new_note_bottom_y[i]), (mask_col.shape[1] - 1, new_note_bottom_y[i]),
                             (125, 125, 125), thickness=3)
                if new_bottom_tail_top_y[i] != 0:
                    cv2.line(mask_col, (0, new_bottom_tail_top_y[i]), (mask_col.shape[1] - 1, new_bottom_tail_top_y[i]),
                             (125, 125, 125), thickness=3)
                if new_bottom_tail_bottom_y[i] != 0:
                    cv2.line(mask_col, (0, new_bottom_tail_bottom_y[i]),
                             (mask_col.shape[1] - 1, new_bottom_tail_bottom_y[i]), (125, 125, 125), thickness=3)

            self._guitar.check_actions()  # FIXME check action

    def play_loop(self):
        frame = np.empty(self._s_feed.frame_shape, dtype=np.uint8)
        frame_columns = np.array_split(frame, 5, axis=1)  # produces evenly spaced column views into frame
        mask = np.empty(self._s_feed.frame_shape[:2], dtype=np.uint8)
        mask_columns = np.array_split(mask, 5, axis=1)  # produces evenly spaced column views into mask
        new_note_bottom_y = np.zeros(5, dtype=int)
        new_bottom_tail_top_y = np.zeros(5, dtype=int)
        new_bottom_tail_bottom_y = np.zeros(5, dtype=int)

        tail_gap_cutoff = frame.shape[0] - settings.NOTE_TAIL_GAP
        group_note_thresh = frame.shape[0] - settings.NOTE_GROUP_HEIGHT

        cv2.namedWindow("mask_feed")
        cv2.setWindowProperty("mask_feed", cv2.WND_PROP_TOPMOST, 1)

        while True:
            # TODO - better incorporate the FIXME check action checks
            self._s_feed.put_next_frame(frame)

            self._guitar.check_actions()  # FIXME check action

            for i in range(5):
                self._c_cap.mask(frame_columns[i], i, mask_columns[i])

                self._guitar.check_actions()  # FIXME check actions

            self._get_note_positions(mask_columns, new_note_bottom_y, new_bottom_tail_top_y, new_bottom_tail_bottom_y)

            # true values mean play the note, false values mean don't play it
            hold_notes = self._old_note_bottom_y > new_note_bottom_y
            if np.any(hold_notes):
                other_group_hold_notes = new_note_bottom_y > group_note_thresh
                self._guitar.add_hold_and_strum(hold_notes | other_group_hold_notes)
                new_note_bottom_y[other_group_hold_notes] = 0

            release_notes = (new_bottom_tail_bottom_y < tail_gap_cutoff) | (
                    self._old_bottom_tail_top_y > new_bottom_tail_top_y)
            if np.any(release_notes):
                self._guitar.add_release(release_notes)

            self._guitar.check_actions()  # FIXME check action

            np.copyto(self._old_note_bottom_y, new_note_bottom_y)
            np.copyto(self._old_bottom_tail_top_y, new_bottom_tail_top_y)
            np.copyto(self._old_bottom_tail_bottom_y, new_bottom_tail_bottom_y)

            cv2.line(mask, (0, group_note_thresh), (mask.shape[1] - 1, group_note_thresh), (125, 125, 125), thickness=1)
            if settings.SHOW_FEED:
                cv2.imshow("mask_feed", mask)

            self._guitar.check_actions()  # FIXME check action

            k = cv2.waitKey(settings.MS_DELAY)
            if k != -1:
                if k == ord('q'):
                    print("quit.")
                    cv2.destroyAllWindows()
                    break
                elif k == ord('w'):
                    settings.DETECTION_DELAY_NS += 1e6
                    print("Increased strum delay to", settings.DETECTION_DELAY_NS / 1e6, "ms.")
                elif k == ord('s'):
                    settings.DETECTION_DELAY_NS -= 1e6
                    print("Decreased strum delay to", settings.DETECTION_DELAY_NS / 1e6, "ms.")


# returns true if yes, false if no
def prompt_yn(prompt):
    response = ""
    while response.lower() not in ('y', 'n'):
        response = input(prompt)
    return response.lower() == 'y'


def main():
    try:
        do_previews = not prompt_yn("Skip previews of screen feed and color capture? (y/n) ")
        load_sfp = prompt_yn("Load screen feed properties from file? (y/n) ")
        load_ccp = prompt_yn("Load color capture properties from file? (y/n) ")

        hero = Hero(do_previews, load_sfp, load_ccp)
        hero.play_loop()
    finally:
        release_all()


if __name__ == "__main__":
    main()
