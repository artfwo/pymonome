#! /usr/bin/env python

import time, random, threading, monome

class Fader(threading.Thread):
    def __init__(self, monome, x):
        threading.Thread.__init__(self)
        self.daemon = True
        self.monome = monome
        self.x = x
        self.goal = 0
        self.now = 0
    
    def run(self):
        self.running = True
        while self.running:
            if self.goal != self.now:
                self.now += 1 if self.now < self.goal else -1
                coldata = ([0] * 8)
                for i in range(self.now+1):
                    coldata[i] = 1
                coldata.reverse()
                self.monome.led_col(self.x, 0, monome.pack_row(coldata))
            time.sleep(1.0/16)

class FadersApp(monome.Monome):
    def __init__(self, host, port):
        monome.Monome.__init__(self, host, port)
        self.faders = [Fader(self, i) for i in range(8)]
        for f in self.faders:
            f.start()
    
    def grid_key(self, x, y, s):
        if s:
            self.faders[x].goal = 7 - y

# try to find a monome (you can skip this if you already know the host/port)
print "looking for a monome..."
host, port = monome.find_any_monome()
print "found!"

m = FadersApp('localhost', port)
m.start()

m.led_all(0)
try:
    while True:
        for i in range(8):
            time.sleep(1.0/20)
except KeyboardInterrupt:
    m.led_all(0)
    m.close()

