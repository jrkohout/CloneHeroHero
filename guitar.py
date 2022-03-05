# guitar.py - represents a guitar hero guitar. Sends (delayed) keypresses when told to strum.

import time
import numpy as np
from queue import SimpleQueue
from pyKey import pressKey, releaseKey, press
from threading import Thread

import settings


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
                while time.perf_counter_ns() - call_time < settings.STRUM_DELAY_NS:  # TODO - I think this busy-wait is killing the performance
                    pass
                # strum the notes
                notes = settings.NOTE_KEYS[note_mask]
                for note in notes:
                    pressKey(note)
                press(settings.STRUM_KEY)
                for note in notes:
                    releaseKey(note)

    # start the guitar's check_strum loop
    def start_thread(self):
        self._thread.start()
        print("Started guitar thread.")

    # enqueues the end-signal to terminate check_strum(), joins with it
    def end_thread(self):
        self._strum_queue.put((False, 0, np.zeros(5).astype(bool)))
        self._thread.join()
        print("Terminated guitar thread.")
