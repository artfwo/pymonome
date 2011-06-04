#! /usr/bin/env python

import time, random
from monome import Monome, MonomeBrowser, find_monome

# try to find a monome (you can skip this if you already know the host/port)
host, port = find_monome('a40h-458')
m = Monome('localhost', port)
m.start()

def mycallback(addr, data):
    x, y, s = data
    m.led_set(x, y, s)

m.app_callback = mycallback

m.led_all(0)
try:
    while True:
        for i in range(8):
            m.led_row(0, i, random.randint(0,255))
            time.sleep(1.0/20)
except KeyboardInterrupt:
    m.led_all(0)
    m.close()

