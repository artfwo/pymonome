#! /usr/bin/env python3

import asyncio
import monome

from life import Life

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
