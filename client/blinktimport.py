import random
import time
from blinkt import set_all, set_clear_on_exit, set_brightness, set_pixel, show, clear #Blinkt LED (requires Git Clone)

#LED CONTROL
def ledstage( stage ):

        #Prevent the LED's clearing after script execution and reboot.
        set_clear_on_exit(False)

        #Colours!
        colours = []
        colours.append([255,25,0])
        colours.append([200,50,0])
        colours.append([150,75,0])
        colours.append([125,100,0])
        colours.append([100,125,0])
        colours.append([50,175,0])
        colours.append([25,200,0])
        colours.append([0,255,0])

        #Loop var
        x = 0

        #Clear LED's if 0
        if stage == 0:
                set_all(0,0,0)
                show()
        elif stage == 8:
                #Party!
                counter = 50
                while x < counter:
                        for i in range(8):
                                set_pixel(i, random.randint(0,255), random.randint(0,255), random.randint(0,255))
                        show()
                        time.sleep(0.05)
                        x += 1
        else:
                while x < stage:
                        set_pixel(x,colours[x][0],colours[x][1],colours[x][2],0.1)
                        show()
                        x += 1

def ledclear():
        set_all(0,0,0)
        show()
