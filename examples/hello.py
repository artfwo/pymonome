#! /usr/bin/env python3

import asyncio
import monome

class Hello(monome.App):
    def on_grid_key(self, x, y, s):
        self.grid.led_set(x, y, s)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    hello_app = Hello()
    asyncio.async(monome.SerialOsc.create(loop=loop, autoconnect_app=hello_app))
    loop.run_forever()
