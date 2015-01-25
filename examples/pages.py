#! /usr/bin/env python3

import asyncio
import monome

from faders import Faders
class FadersPage(monome.Page, Faders):
    def __init__(self, pages):
        monome.Page.__init__(self, pages)
        Faders.__init__(self)

    def ready(self):
        monome.Page.ready(self)
        Faders.ready(self)

from lights import Lights
class LightsPage(monome.Page, Lights):
    def __init__(self, manager):
        monome.Page.__init__(self, manager)
        Lights.__init__(self)

    def ready(self):
        monome.Page.ready(self)
        Lights.ready(self)

from life import Life
class LifePage(monome.Page, Life):
    def __init__(self, manager):
        monome.Page.__init__(self, manager)
        Life.__init__(self)

    def ready(self):
        monome.Page.ready(self)
        Life.ready(self)

from hello import Hello
class HelloPage(monome.Page, Hello):
    def __init__(self, manager):
        monome.Page.__init__(self, manager)
        Hello.__init__(self)

    def ready(self):
        monome.Page.ready(self)
        Hello.ready(self)

class ExamplePages(monome.SumPageManager):
    def __init__(self):
        super().__init__([
            FadersPage(self),
            LightsPage(self),
            LifePage(self),
            HelloPage(self),
        ])

    def grid_key(self, x, y, s):
        super().grid_key(x, y, s)

loop = asyncio.get_event_loop()
asyncio.async(monome.create_serialosc_connection(ExamplePages, loop=loop))

try:
    loop.run_forever()
except KeyboardInterrupt:
    print('kthxbye')
