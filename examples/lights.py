#! /usr/bin/env python3

import random
import asyncio
import monome

class Lights(monome.Monome):
    def __init__(self):
        super().__init__('/lights')

    def ready(self):
        self.alive = True
        asyncio.async(self.animate())

    def grid_key(self, x, y, s):
        if s == 1:
            self.led_set(x, y, s)

    def disconnect(self, *args):
        self.alive = False
        super().disconnect(*args)

    @asyncio.coroutine
    def animate(self):
        while self.alive:
            for i in range(self.height):
                row = [random.randint(0, 1) for i in range(self.width)]
                for j in range(3):
                    self.led_row(0, i, [0] * self.width)
                    yield from asyncio.sleep(1 / 30)
                    self.led_row(0, i, row)
                    yield from asyncio.sleep(1 / 30)
            for i in reversed(range(self.height)):
                row = [random.randint(0, 1) for i in range(self.width)]
                self.led_row(0, i, row)
                yield from asyncio.sleep(1 / 20)
            yield from asyncio.sleep(2)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    asyncio.async(monome.create_serialosc_connection(Lights), loop=loop)
    loop.run_forever()
