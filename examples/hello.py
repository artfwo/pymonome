#! /usr/bin/env python3

import asyncio
import monome

class HelloApp(monome.GridApp):
    def on_grid_key(self, x, y, s):
        self.grid.led_set(x, y, s)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    hello_app = HelloApp()

    def serialosc_device_added(id, type, port):
        print('connecting to {} ({})'.format(id, type))
        asyncio.ensure_future(hello_app.grid.connect('127.0.0.1', port))

    serialosc = monome.SerialOsc()
    serialosc.device_added_event.add_handler(serialosc_device_added)

    loop.run_until_complete(serialosc.connect())

    loop.run_forever()
