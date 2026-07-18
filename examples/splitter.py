#! /usr/bin/env python3

import asyncio
import monome

from life import Life

async def main():
    section1 = monome.GridSection((8, 8), (0, 0))
    section2 = monome.GridSection((8, 8), (8, 0))
    splitter = monome.GridSplitter([section1, section2])

    life1 = Life()
    life1.set_grid(section1)

    life2 = Life()
    life2.set_grid(section2)

    serialosc = monome.SerialOsc()
    serialosc.bind(splitter.grid)
    await serialosc.connect()

    await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(main())
