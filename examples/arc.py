#! /usr/bin/env python3
#
# Test for a push-button monome arc

import asyncio
import monome
import random

def clamp(value, min_value, max_value):
    return max(min(value, max_value), min_value)

class ArcTest(monome.ArcApp):
    def __init__(self):
        super().__init__()
        self.pos = [0, 0, 0, 0]

    def on_arc_ready(self):
        for ring in range(0, 4):
            self.render_ring(ring)

    def on_arc_delta(self, ring, delta):
        self.pos[ring] = clamp(self.pos[ring] + delta, 0, 63)
        self.render_ring(ring)

    def on_arc_key(self, _, s):
        if s > 0:
            for ring in range(4):
                self.pos[ring] = random.randint(0, 63)
                self.render_ring(ring)

    def render_ring(self, ring):
        leds = [15 if i <= self.pos[ring] else 1 for i in range(64)]
        self.arc.ring_map(ring, leds)

    def cleanup(self):
        if self.arc.connected:
            for ring in range(0, 4):
                self.arc.ring_all(ring, 0)

async def main():
    app = ArcTest()

    serialosc = monome.SerialOsc()
    serialosc.bind(app.arc)
    await serialosc.connect()

    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        app.cleanup()

if __name__ == '__main__':
    asyncio.run(main())
