#! /usr/bin/env python3

import asyncio
import monome

class HelloApp(monome.GridApp):
    def on_grid_key(self, x, y, s):
        self.grid.led_set(x, y, s)

async def main():
    hello_app = HelloApp()

    serialosc = monome.SerialOsc()
    serialosc.bind(hello_app.grid)
    await serialosc.connect()

    await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(main())
