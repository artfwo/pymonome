#! /usr/bin/env python3

import random
import asyncio
import monome

from perlin_noise import PerlinNoise

class PerinApp(monome.GridApp):
    def __init__(self):
        super().__init__()
        self.noise = PerlinNoise()
        self.buffer = monome.GridBuffer(16, 16)
        self.task = asyncio.create_task(asyncio.sleep(0))

    def on_grid_ready(self):
        self.alive = True
        self.task = asyncio.create_task(self.animate())

    def on_grid_key(self, x, y, s):
        if s == 1:
            self.grid.led_set(x, y, s)

    def on_grid_disconnect(self, *args):
        self.alive = False
        self.task.cancel()

    async def animate(self):
        delta_x = 0
        delta_y = 0
        delta_z = 0

        while self.alive:
            for x in range(16):
                for y in range(16):
                    value = self.noise([x / 16, y / 16, delta_z]) * 16

                    if value < 0:
                        value = 0
                    else:
                        value = int(value)
                    # if value < 0:
                        # print(value)
                    self.buffer.led_level_set(x, y, value)

            self.buffer.render(self.grid)

            delta_z += 0.0125

            await asyncio.sleep(0.05)

async def main():
    loop = asyncio.get_running_loop()
    app = PerinApp()

    def serialosc_device_added(id, type, port):
        print('connecting to {} ({})'.format(id, type))
        asyncio.create_task(app.grid.connect('127.0.0.1', port))

    serialosc = monome.SerialOsc()
    serialosc.device_added_event.add_handler(serialosc_device_added)

    await serialosc.connect()
    await loop.create_future()

if __name__ == '__main__':
    asyncio.run(main())
