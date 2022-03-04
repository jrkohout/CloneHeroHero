# guitar.py - represents a guitar hero guitar. Sends (delayed) keypresses when told to strum.

import time
import numpy as np
from queue import SimpleQueue
from pyKey import pressKey, releaseKey, press
from threading import Thread

STRUM_DELAY_MS = 10
STRUM_DELAY_NS = STRUM_DELAY_MS * 1e6

# in-game keybinds for green, red, yellow, blue, and orange, respectively
NOTE_KEYS = np.array(['a', 's', 'j', 'k', 'l'])
#                  |== G == R == Y == B == O ===========*==*==*==*==*=======-----=====|

STRUM_KEY = 'DOWN'


class Guitar:
    def __init__(self):
        # use .appendleft() to push, .pop() to pop, and [-1] to peek
        self._strum_queue = SimpleQueue()
        self._thread = Thread(target=self.check_strum)

    # only push a note mask if at least one note is to be strummed
    def enqueue_strum(self, note_list):
        self._strum_queue.put((True, time.perf_counter_ns(), note_list))  # True - continue

    def check_strum(self):
        keep_looping = True
        while keep_looping:
            keep_looping, call_time, note_mask = self._strum_queue.get()
            if keep_looping:
                # wait until the delay has passed
                while time.perf_counter_ns() - call_time < STRUM_DELAY_NS:
                    pass
                # strum the notes
                notes = NOTE_KEYS[note_mask]
                for note in notes:
                    pressKey(note)
                press(STRUM_KEY)
                for note in notes:
                    releaseKey(note)
        self._thread.join()

    # start the guitar's check_strum loop
    def start_thread(self):
        self._thread.start()
        print("Started guitar thread")

    # enqueues the end-signal to have check_strum() terminate and join
    def end_thread(self):
        self._strum_queue.put((False, 0, np.zeros(5).astype(bool)))
