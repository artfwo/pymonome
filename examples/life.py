#! /usr/bin/env python3
#
# based on life64.ck monome app by tehn

import asyncio
import monome
import copy, itertools, random

class Life(monome.Monome):
    def __init__(self):
        super().__init__('/life')
        self.alive = True

    def ready(self):
        self.world = [[0 for col in range(self.width)] for row in range(self.height)]
        self.task = asyncio.async(self.begin())

    def disconnect(self):
        super().disconnect()
        self.task.cancel()
        self.led_all(0)

    def grid_key(self, x, y, s):
        if x == self.width - 1 and y == 0 and s == 1:
            self.alive = not self.alive
            self.led_set(self.width - 1, 0, int(not self.alive))
            return
        if s == 1:
            row, col = y, x
            self.world[row][col] ^= 1
            self.led_set(x, y, self.world[row][col])
        else:
            pass

    @asyncio.coroutine
    def begin(self):
        while True:
            if self.alive:
                self.update()
                for i, row in enumerate(self.world):
                    self.led_row(0, i, row)
            yield from asyncio.sleep(0.2)

    def update(self):
        def neighbors(x, y):
            result = 0
            for dx, dy in [d for d in itertools.product([-1, 0, 1], repeat=2) if d != (0, 0)]:
                row = (y + dy) % self.height
                col = (x + dx) % self.width
                result += self.world[row][col]
            return result

        new_world = copy.deepcopy(self.world)
        for x in range(self.width):
            for y in range(self.height):
                n = neighbors(x, y)
                row, col = y, x
                if n == 3:
                    new_world[row][col] = 1
                elif (n < 2 or n > 3):
                    new_world[row][col] = 0
        self.world = copy.deepcopy(new_world)

    def randomize(self):
        for row in range(self.height):
            for col in range(self.width):
                self.world[row][col] = random.randint(0, 1)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    asyncio.async(monome.create_serialosc_connection(Life), loop=loop)
    loop.run_forever()
