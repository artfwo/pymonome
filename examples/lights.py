#! /usr/bin/env python3

import random
import asyncio
import monome

class Lights(monome.GridApp):
    def __init__(self):
        super().__init__()
        self.task = asyncio.ensure_future(asyncio.sleep(0))

    def on_grid_ready(self):
        self.alive = True
        self.task = asyncio.ensure_future(self.animate())

    def on_grid_key(self, x, y, s):
        if s == 1:
            self.grid.led_set(x, y, s)

    def on_grid_disconnect(self, *args):
        self.alive = False
        self.task.cancel()

    async def animate(self):
        while self.alive:
            for i in range(self.grid.height):
                row = [random.randint(0, 1) for i in range(self.grid.width)]
                for j in range(3):
                    self.grid.led_row(0, i, [0] * self.grid.width)
                    await asyncio.sleep(1 / 30)
                    self.grid.led_row(0, i, row)
                    await asyncio.sleep(1 / 30)
            for i in reversed(range(self.grid.height)):
                row = [random.randint(0, 1) for i in range(self.grid.width)]
                self.grid.led_row(0, i, row)
                await asyncio.sleep(1 / 20)
            await asyncio.sleep(2)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    lights = Lights()

    def serialosc_device_added(id, type, port):
        print('connecting to {} ({})'.format(id, type))
        asyncio.ensure_future(lights.grid.connect('127.0.0.1', port))

    serialosc = monome.SerialOsc()
    serialosc.device_added_event.add_handler(serialosc_device_added)

    loop.run_until_complete(serialosc.connect())

    loop.run_forever()
