#! /usr/bin/env python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#
# rove_bridge by artfwo - a proxy for apps
# that have static i/o ports such as rove and duplex
#
# usage:
#   ./rove_bridge.py <device-id> <listen-port> <app-port> <prefix>
# example:
#   ./rove_bridge.py a40h-002 8080 8000 /rove

import argparse, monome, OSC

class BridgeFrontend(OSC.OSCServer):
    def __init__(self, server_address, app_address, prefix):
        OSC.OSCServer.__init__(self, server_address)

        self.prefix = prefix
        self.client.connect(app_address)
        self.addMsgHandler('default', self.bridge_handler)

    def bridge_handler(self, addr, tags, data, client_address):
        global backend
        msg = OSC.OSCMessage(addr.replace(self.prefix, backend.prefix, 1))
        map(msg.append, data)
        backend.client.send(msg)

class BridgeBackend(monome.Monome):
    def __init__(self, address):
        monome.Monome.__init__(self, address)
    
    def monome_handler(self, addr, tags, data, client_address):
        global frontend
        msg = OSC.OSCMessage(addr.replace(self.prefix, frontend.prefix, 1))
        map(msg.append, data)
        frontend.client.send(msg)

parser = argparse.ArgumentParser()
#parser.add_argument('-m', '--monomeserial', dest='monomeserial', action='store_true',
#                    help='use the monomeserial protocol to talk to the app')
parser.add_argument('device_id')
parser.add_argument('listen_port', type=int)
parser.add_argument('app_port', type=int)
parser.add_argument('prefix')
args = parser.parse_args()

print "connecting to %s..." % args.device_id
monome_address = monome.find_monome(args.device_id)
print "connected!"

backend = BridgeBackend(monome_address)
frontend = BridgeFrontend(('', args.listen_port), ('', args.app_port), args.prefix)

import select
try:
    while True:
        ready = select.select([backend, frontend], [], [], None)[0]
        for r in ready:
            r.handle_request()
except KeyboardInterrupt:
    print "kthxbye"