#! /usr/bin/env python3

import asyncio
import monome

from life import Life

async def main():
    loop = asyncio.get_running_loop()

    pages = monome.SumGridPageManager(2)

    life1 = Life()
    life1.set_grid(pages.pages[0])

    life2 = Life()
    life2.set_grid(pages.pages[1])

    def serialosc_device_added(id, type, port):
        print('connecting to {} ({})'.format(id, type))
        asyncio.create_task(pages.grid.connect('127.0.0.1', port))

    serialosc = monome.SerialOsc()
    serialosc.device_added_event.add_handler(serialosc_device_added)

    await serialosc.connect()
    await loop.create_future()

if __name__ == '__main__':
    asyncio.run(main())
