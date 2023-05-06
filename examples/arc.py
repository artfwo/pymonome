#! /usr/bin/env python3
#
# Test for a push-button monome arc

import asyncio
import monome


class ExampleArcApp(monome.ArcApp):
    def __init__(self):
        super().__init__()
        self.pos = [0, 0, 0, 0]

    def on_arc_ready(self):
        print('Ready, clearing all rings...')
        for n in range(0, 4):
            self.arc.ring_all(n, 0)

    def on_arc_disconnect(self):
        print('Arc disconnected.')

    def on_arc_delta(self, ring, delta):
        print(f'Ring: {ring} Delta: {delta}')

        old_pos = self.pos[ring]
        new_pos = old_pos + delta

        if new_pos > old_pos:
            self.arc.ring_range(ring, old_pos, new_pos, 15)
        else:
            self.arc.ring_range(ring, new_pos, old_pos, 5)

        self.pos[ring] = new_pos

    def on_arc_key(self, ring, s):
        print(f'Ring: {ring} Pressed: {s > 0}')
        self.arc.ring_all(ring, 15 if s > 0 else 0)


async def main():
    loop = asyncio.get_running_loop()
    app = ExampleArcApp()

    def serialosc_device_added(id, type, port):
        if 'arc' not in type:
            print(f'ignoring {id} ({type}) as device does not appear to be an arc')
            return

        print(f'connecting to {id} ({type})')
        asyncio.create_task(app.arc.connect('127.0.0.1', port))

    serialosc = monome.SerialOsc()
    serialosc.device_added_event.add_handler(serialosc_device_added)

    await serialosc.connect()
    await loop.create_future()

if __name__ == '__main__':
    asyncio.run(main())
