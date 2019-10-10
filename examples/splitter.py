#! /usr/bin/env python3

import asyncio
import monome

from life import Life

class SplitterSerialOsc(monome.SerialOsc):
    def __init__(self, app1, app2, loop=None, autoconnect_app=None):
        super().__init__(loop, autoconnect_app)
        self.app1 = app1
        self.app2 = app2

    async def splitter_connect(self, port):
        transport, grid = await self.loop.create_datagram_endpoint(monome.Grid, local_addr=('127.0.0.1', 0), remote_addr=('127.0.0.1', port))

        section1 = monome.GridSection((8, 8), (0, 0))
        section2 = monome.GridSection((8, 8), (8, 0))
        splitter = monome.Splitter(grid, [section1, section2])

        self.app1.attach(section1)
        self.app2.attach(section2)

        splitter.connect()

    def on_device_added(self, id, type, port):
        if type == "monome 128":
            asyncio.async(self.splitter_connect(port))

if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    section1 = monome.GridSection((8, 8), (0, 0))
    section2 = monome.GridSection((8, 8), (8, 0))
    splitter = monome.GridSplitter([section1, section2])

    life1 = Life()
    life1.set_grid(section1)

    life2 = Life()
    life2.set_grid(section2)

    def serialosc_device_added(id, type, port):
        print('connecting to {} ({})'.format(id, type))
        asyncio.ensure_future(splitter.grid.connect('127.0.0.1', port))

    serialosc = monome.SerialOsc()
    serialosc.device_added_event.add_handler(serialosc_device_added)

    loop.run_until_complete(serialosc.connect())

    loop.run_forever()
