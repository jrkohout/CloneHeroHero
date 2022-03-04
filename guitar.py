# guitar.py - represents a guitar hero guitar. Sends (delayed) keypresses when told to strum.

import time
import numpy as np
from collections import deque
from pyKey import pressKey, releaseKey, press, sendSequence, showKeys

STRUM_DELAY_MS = 0
STRUM_DELAY_NS = STRUM_DELAY_MS * 1e6

# in-game keybinds for green, red, yellow, blue, and orange, respectively
NOTE_KEYS = np.array(['a', 's', 'j', 'k', 'l'])
#                  |== G == R == Y == B == O ===========*==*==*==*==*=======-----=====|

STRUM_KEY = 'DOWN'


class Guitar:
    def __init__(self):
        # use .appendleft() to push, .pop() to pop, and [-1] to peek
        self._strum_queue = deque()

    # only push a note mask if at least one note is to be strummed
    def push_strum(self, note_list):
        self._strum_queue.appendleft((time.perf_counter_ns(), note_list))

    def check_strum(self):  # TODO - this could potentially be run constantly on another thread (using proper synchronization constructs)
        if len(self._strum_queue) > 0:
            call_time = self._strum_queue[-1][0]
            if time.perf_counter_ns() - call_time >= STRUM_DELAY_NS:
                _, note_mask = self._strum_queue.pop()
                notes = NOTE_KEYS[note_mask]
                for note in notes:
                    pressKey(note)
                press(STRUM_KEY)
                for note in notes:
                    releaseKey(note)
