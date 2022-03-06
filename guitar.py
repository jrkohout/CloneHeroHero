# guitar.py - represents a guitar hero guitar. Sends (delayed) keypresses when told to strum.

import time
from collections import deque
from pyKey import pressKey, releaseKey, press

import settings


class Guitar:
    def __init__(self):
        # use .appendleft() to push, .pop() to pop, and [-1] to peek
        self._strum_queue = deque()

    # only push a note mask if at least one note is to be strummed
    def enqueue_strum(self, note_mask):
        # items: (call_time, note_mask)
        self._strum_queue.appendleft((time.perf_counter_ns(), note_mask))  # TODO - could use better optimized queue

    def check_strum(self):
        # only strum if the delay has passed
        if len(self._strum_queue) > 0 and time.perf_counter_ns() - self._strum_queue[-1][0] >= settings.STRUM_DELAY_NS:  # TODO - could use better checks
            _, note_mask = self._strum_queue.pop()

            # TODO - could MAYBE have a thread block for a signal on get(), and only send a signal to play the notes
            #  when the delay has passed in the many check_strum calls currently in main. This would prevent the main
            #  thread from having to strum the notes, which might could possibly take some time. Though with the other
            #  threading experiments, this seems unlikely to help (but I haven't tried on a powerful PC).

            # strum the notes
            notes = settings.NOTE_KEYS[note_mask]
            for note in notes:
                pressKey(note)
            press(settings.STRUM_KEY)
            for note in notes:
                releaseKey(note)
