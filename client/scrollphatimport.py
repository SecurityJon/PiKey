import math
import sys
import time

import scrollphat

#LED CONTROL
def ledstage( stage ):

        pause_time = 0.03
        scrollphat.set_brightness(2)

        for y in range(5):
                for x in range(stage):
                        scrollphat.set_pixel(x,y,1)
                        scrollphat.update()
                        time.sleep(pause_time)
def ledclear():
        scrollphat.clear()
