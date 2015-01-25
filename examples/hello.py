#! /usr/bin/env python3

import asyncio
import monome

class Hello(monome.Monome):
    def __init__(self):
        super().__init__('/hello')

    def grid_key(self, x, y, s):
        self.led_set(x, y, s)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    asyncio.async(monome.create_serialosc_connection(Hello, loop=loop))
    loop.run_forever()
