#! /usr/bin/env python3
#
# rove_bridge by artfwo - a proxy for monome apps that have
# static i/o ports such as rove and duplex
#
# usage:
#   ./rove_bridge.py <device-id> <listen-port> <app-port> <prefix>
# example:
#   ./rove_bridge.py a40h-002 8080 8000 /rove

import asyncio
import aiosc
import itertools
import monome

class Gate(aiosc.OSCProtocol):
    def __init__(self, prefix, bridge):
        self.prefix = prefix.strip('/')
        self.bridge = bridge
        super().__init__(handlers={
            '/{}/grid/led/set'.format(self.prefix):
                lambda addr, path, x, y, s:
                    self.bridge.led_set(x, y, s),
            '/{}/grid/led/all'.format(self.prefix):
                lambda addr, path, s:
                    self.bridge.led_all(s),
            '/{}/grid/led/map'.format(self.prefix):
                lambda addr, path, x_offset, y_offset, *s:
                    self.bridge.led_map(x_offset, y_offset, list(itertools.chain(*[monome.unpack_row(r) for r in s]))),
            '/{}/grid/led/row'.format(self.prefix):
                lambda addr, path, x_offset, y, *s:
                    self.bridge.led_row(x_offset, y, list(itertools.chain(*[monome.unpack_row(r) for r in s]))),
            '/{}/grid/led/col'.format(self.prefix):
                lambda addr, path, x, y_offset, *s:
                    self.bridge.led_col(x, y_offset, list(itertools.chain(*[monome.unpack_row(r) for r in s]))),
            '/{}/grid/led/intensity'.format(self.prefix):
                lambda addr, path, i:
                    self.bridge.led_intensity(i),
            '/{}/tilt/set'.format(self.prefix):
                lambda addr, path, n, s:
                    self.bridge.tilt_set(n, s),
        })

    def grid_key(self, x, y, s):
        self.send('/{}/grid/key'.format(self.prefix), x, y, s)

class Bridge(monome.Monome):
    def __init__(self, loop=None):
        super().__init__('/rove-bridge')
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop

    def ready(self):
        asyncio.async(self.init_gate())

    @asyncio.coroutine
    def init_gate(self):
        transport, protocol = yield from self.loop.create_datagram_endpoint(
            lambda: Gate('/rove', self),
            local_addr=('127.0.0.1', 8080),
            remote_addr=('127.0.0.1', 8000)
        )
        self.gate = protocol

    def grid_key(self, x, y, s):
        self.gate.grid_key(x, y, s)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    asyncio.async(monome.create_serialosc_connection(Bridge), loop=loop)
    loop.run_forever()
