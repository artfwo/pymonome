#! /usr/bin/env python3

import asyncio
import monome

class Hello(monome.Monome):
    def __init__(self):
        super().__init__('/hello')

    def grid_key(self, x, y, s):
        self.led_row(0, y, [s] * 8)
        self.led_col(x, 0, [s] * 8)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    asyncio.async(monome.create_serialosc_connection(Hello, loop=loop))
    loop.run_forever()
