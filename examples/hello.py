#! /usr/bin/env python

import time, random
from monome import Monome, MonomeBrowser, find_monome

# try to find a monome (you can skip this if you already know the host/port)
print "looking for a monome..."
host, port = find_any_monome()
print "found!"

m = Monome('localhost', port)
m.start()

def mycallback(x, y, s):
    m.led_set(x, y, s)

m.grid_key = mycallback

m.led_all(0)
try:
    while True:
        for i in range(8):
            m.led_row(0, i, random.randint(0,255))
            time.sleep(1.0/20)
except KeyboardInterrupt:
    m.led_all(0)
    m.close()

