# guitar.py - represents a guitar hero guitar. Sends (delayed) keypresses when told to strum.

# strum_counter = 0
# todo maybe remove these? don't want much delay
# STRUMS_PER_SECOND = 6
# STRUM_DELAY_NS = 1 / STRUMS_PER_SECOND * 1e9
STRUM_KEY = 'DOWN'
cidx2key = {  # todo could probably change this to an array
    0: 'g',  # green
    1: 'f',  # red
    2: 'd',  # yellow
    3: 's',  # blue
    4: 'a'   # orange
}


class Guitar:
    def __init__(self):
        pass

    def strum(self, notes):
        pass




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