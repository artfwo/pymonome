#! /usr/bin/env python3

import asyncio
import monome

from faders import Faders
class FadersPart(monome.Section, Faders):
    def __init__(self, splitter, size, offset):
        monome.Section.__init__(self, splitter, size, offset)
        Faders.__init__(self)

    def ready(self):
        monome.Section.ready(self)
        Faders.ready(self)

from lights import Lights
class LightsPart(monome.Section, Lights):
    def __init__(self, splitter, size, offset):
        monome.Section.__init__(self, splitter, size, offset)
        Lights.__init__(self)

    def ready(self):
        monome.Section.ready(self)
        Lights.ready(self)

class ExampleSplitter(monome.Splitter):
    def __init__(self):
        super().__init__([
            FadersPart(self, size=(8,8), offset=(0,0)),
            LightsPart(self, size=(8,8), offset=(8,0)),
        ])

loop = asyncio.get_event_loop()
asyncio.async(monome.create_serialosc_connection(ExampleSplitter, loop=loop))

try:
    loop.run_forever()
except KeyboardInterrupt:
    print('kthxbye')
