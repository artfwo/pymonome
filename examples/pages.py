#! /usr/bin/env python3

import asyncio
import monome

from life import Life

class PagesSerialOsc(monome.SerialOsc):
    def __init__(self, app1, app2, loop=None, autoconnect_app=None):
        super().__init__(loop, autoconnect_app)
        self.app1 = app1
        self.app2 = app2

    async def pages_connect(self, port):
        transport, grid = await self.loop.create_datagram_endpoint(monome.Grid, local_addr=('127.0.0.1', 0), remote_addr=('127.0.0.1', port))

        page1 = monome.Page()
        page2 = monome.Page()
        page_manager = monome.SeqPageManager(grid=grid, pages=[page1, page2])

        self.app1.attach(page1)
        self.app2.attach(page2)

        page_manager.connect()

    def on_device_added(self, id, type, port):
        asyncio.create_task(self.pages_connect(port))

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
