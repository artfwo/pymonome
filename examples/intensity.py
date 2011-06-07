#! /usr/bin/env python

# just a hack to change led intensity when another app is playing

import sys, time
from OSC import OSCClient, OSCMessage

host, port, prefix = sys.argv[1:]
path = '/%s/grid/led/intensity' % prefix.strip('/')

osc = OSCClient()
osc.connect((host, int(port)))

try:
    while True:
        for i in range(16):
            msg = OSCMessage(path)
            msg.append(i)
            osc.send(msg)
            time.sleep(1.0/64)
        for i in range(16):
            msg = OSCMessage(path)
            msg.append(15 - i)
            osc.send(msg)
            time.sleep(1.0/64)
except KeyboardInterrupt:
    msg = OSCMessage(path)
    msg.append(15)
    osc.send(msg)

