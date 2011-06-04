#! /usr/bin/env python

import time, random
from monome import Monome, MonomeBrowser

# lookup for monome (can skip this if you know the host/port)
serial = 'a40h-458'
browser = MonomeBrowser()
browser.start()
print "looking for %s" % serial
while not browser.devices.has_key(serial):
    time.sleep(0)
print "found!"
host, port = browser.devices[serial]
browser.close()

# connect to the monome
m = Monome('localhost', port) # don't use resolved host, 'cause it doesn't work
m.start() # begin processing callbacks

def mycallback(addr, data):
    x, y, s = data
    m.led_set(x, y, s)

m.app_callback = mycallback

m.led_all(0)
try:
    while True:
        for i in range(8):
            m.led_set(0, 0, random.randint(0,1))
            m.led_set(7, 7, random.randint(0,1))
            time.sleep(1.0/1000)
except KeyboardInterrupt:
    m.led_all(0)
    m.close()

