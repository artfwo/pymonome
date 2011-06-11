#! /usr/bin/env python

import time, random
from monome import Monome, find_any_monome
from OSC import OSCClient, OSCMessage

class Renoise(object):
    def __init__(self, address):
        self.client = OSCClient()
        self.client.connect(address)

    def panic(self):
        self.send_osc('/renoise/transport/panic')
    
    def note_on(self, instrument, track, note, velocity):
        self.send_osc('/renoise/trigger/note_on', instrument, track, note, velocity)
    
    def note_off(self, instrument, track, note):
        self.send_osc('/renoise/trigger/note_off', instrument, track, note)
    
    def send_osc(self, path, *args):
        msg = OSCMessage(path)
        map(msg.append, args)
        self.client.send(msg)

print "looking for a monome..."
host, port = find_any_monome()
print "found!"

r = Renoise(('localhost', 8800))
m = Monome((host, port))
m.start()

def mycallback(x, y, s):
    m.led_set(x, y, s)
    if s == 1:
        r.note_on(-1, -1, x*8+y, 127)
    else:
        r.note_off(-1, -1, x*8+y)

m.grid_key = mycallback

m.led_all(0)
try:
    while True:
        for i in range(8):
            time.sleep(1.0/20)
except KeyboardInterrupt:
    r.panic()
    m.led_all(0)
    m.close()

