#! /usr/bin/env python3
#
# test for automatic varibright->monobright conversion of messages
# try changing varibright to True for smooth brightness transition
#

import asyncio
import monome

class Monobright(monome.Monome):
    def __init__(self):
        super().__init__('/hello', varibright=False)

    @asyncio.coroutine
    def light(self, x, y):
        for i in range(16):
            self.led_level_set(x, y, i)
            yield from asyncio.sleep(0.1)

    def grid_key(self, x, y, s):
        if s == 1:
            asyncio.async(self.light(x, y))

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    asyncio.async(monome.create_serialosc_connection(Monobright, loop=loop))
    loop.run_forever()
