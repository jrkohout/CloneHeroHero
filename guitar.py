# guitar.py - represents a guitar hero guitar. Sends (delayed) keypresses when told to strum.

import time
from collections import deque
from pyKey import pressKey, releaseKey, press
import numpy as np

import settings


def hold(note_mask):
    for note in settings.NOTE_KEYS[note_mask]:
        pressKey(note)


def strum():
    press(settings.STRUM_KEY)


def release(note_mask):
    for note in settings.NOTE_KEYS[note_mask]:
        releaseKey(note)


def release_all():
    release(np.array([True, True, True, True, True]))


# circular queue with parallel time queue
class NoteQueue:
    def __init__(self, num_rows, num_cols):
        self._size = num_rows
        # left-to-right queue: enqueue to left side, dequeue from right side
        self._notes = np.empty((self._size, num_cols), dtype=bool)
        self._left_idx = 0
        self._right_idx = 0
        # times - times when action should be taken on notes in the row
        self._times = deque()  # use .appendleft() to push, .pop() to pop, and [-1] to peek

    def enqueue(self, note_mask):
        self._times.appendleft(time.perf_counter_ns() + settings.STRUM_DELAY_NS)  # action time = current time + delay
        self._notes[self._right_idx] = note_mask
        self._right_idx = (self._right_idx + 1) % self._size

    def dequeue(self):
        self._times.pop()
        note_mask = self._notes[self._left_idx]
        self._left_idx = (self._left_idx + 1) % self._size
        return note_mask

    def get_next_time(self):
        return self._times[-1]

    def is_populated(self):
        return len(self._times) > 0


class Guitar:
    def __init__(self):
        self._hold_notes = NoteQueue(settings.NOTE_QUEUE_SIZE, 5)
        self._release_notes = NoteQueue(settings.NOTE_QUEUE_SIZE, 5)

    def add_release(self, note_mask):
        self._release_notes.enqueue(note_mask)

    def add_hold(self, note_mask):  # currently actually acts like add_hold_and_strum
        self._hold_notes.enqueue(note_mask)

    # TODO - could MAYBE have a thread block for a signal on get(), and only send a signal to play the notes
    #  when the delay has passed in the many check_actions calls currently in main. This would prevent the main
    #  thread from having to pres, strum, and release the notes, which might be taking take some time. Though with
    #  the other threading experiments, this seems unlikely to help (but I haven't tried on a powerful PC).
    def check_actions(self):
        # only perform actions if the delay has passed
        current_time = time.perf_counter_ns()

        # check releases first
        if self._release_notes.is_populated() and current_time >= self._release_notes.get_next_time():
            release(self._release_notes.dequeue())

        # check holds
        if self._hold_notes.is_populated() and current_time >= self._hold_notes.get_next_time():
            hold(self._hold_notes.dequeue())
            strum()  # TODO - untie strum from hold
