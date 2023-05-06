#! /usr/bin/env python3

import random
import asyncio
import monome

FADERS_MAX_VALUE = 100

class Faders(monome.GridApp):
    def __init__(self):
        super().__init__() # TODO: prefix

    def on_grid_ready(self):
        self.grid.led_all(0)

        self.row_values = []
        row_value = 0
        for i in range(self.grid.height):
            self.row_values.append(int(round(row_value)))
            row_value += FADERS_MAX_VALUE / (self.grid.height - 1)

        self.values = [random.randint(0, FADERS_MAX_VALUE) for f in range(self.grid.width)]
        self.faders = [asyncio.create_task(self.fade_to(f, 0)) for f in range(self.grid.width)]

    def on_grid_key(self, x, y, s):
        if s == 1:
            self.faders[x].cancel()
            self.faders[x] = asyncio.create_task(self.fade_to(x, self.row_to_value(y)))

    def value_to_row(self, value):
        return sorted([i for i in range(self.grid.height)], key=lambda i: abs(self.row_values[i] - value))[0]

    def row_to_value(self, row):
        return self.row_values[self.grid.height - 1 - row]

    async def fade_to(self, x, new_value):
        while self.values[x] != new_value:
            if self.values[x] < new_value:
                self.values[x] += 1
            else:
                self.values[x] -= 1
            col = [0 if c > self.value_to_row(self.values[x]) else 1 for c in range(self.grid.height)]
            col.reverse()
            self.grid.led_col(x, 0, col)
            await asyncio.sleep(1/100)

async def main():
    loop = asyncio.get_running_loop()
    faders_app = Faders()

    def serialosc_device_added(id, type, port):
        print('connecting to {} ({})'.format(id, type))
        asyncio.create_task(faders_app.grid.connect('127.0.0.1', port))

    serialosc = monome.SerialOsc()
    serialosc.device_added_event.add_handler(serialosc_device_added)

    await serialosc.connect()
    await loop.create_future()

if __name__ == '__main__':
    asyncio.run(main())
