#! /usr/bin/env python3

import asyncio
import monome

from life import Life

async def main():
    pages = monome.SumGridPageManager(2)

    life1 = Life()
    life1.set_grid(pages.pages[0])

    life2 = Life()
    life2.set_grid(pages.pages[1])

    serialosc = monome.SerialOsc()
    serialosc.bind(pages.grid)
    await serialosc.connect()

    await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(main())
