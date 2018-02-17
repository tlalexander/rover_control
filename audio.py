from array import array
import pygame
from pygame.mixer import Sound, get_init,  pre_init
import time

class Note(pygame.mixer.Sound):

    def __init__(self, frequency, volume=.1):
        self.frequency = frequency
        Sound.__init__(self, self.build_samples())
        self.set_volume(volume)

    def build_samples(self):
        period = int(round(get_init()[0] / self.frequency))
        samples = array("h", [0] * period)
        amplitude = 2 ** (abs(get_init()[1]) - 1) - 1
        for time in range(period):
            if time < period / 2:
                samples[time] = amplitude
            else:
                samples[time] = -amplitude
        return samples
pre_init(44100, -16, 1, 1024)
pygame.init()

sounds = {}
keymap = {
    pygame.K_z: 880,
    pygame.K_x: 440
}


# note = Note(440)
# note.play(-1)
# time.sleep(.2)
#
# note = Note(880)
# note.play(-1)
# time.sleep(.2)
#
# note = Note(1660)
# note.play(-1)
# time.sleep(.2)
#
# note = Note(3000)
# note.play(-1)
# time.sleep(.1)

import os
os.system("beep -f 440 -l 100")
os.system("beep -f 1200 -l 200")
os.system("beep -f 3000 -l 100")
os.system("beep -f 440 -l 1000")


pygame.quit()
