# pymonome - library for interfacing with monome devices
#
# Copyright (c) 2011-2014 Artem Popov <artfwo@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import asyncio, aiosc
import itertools

def pack_row(row):
    return row[7] << 7 | row[6] << 6 | row[5] << 5 | row[4] << 4 | row[3] << 3 | row[2] << 2 | row[1] << 1 | row[0]

def unpack_row(val):
    return [
        val & 1,
        val >> 1 & 1,
        val >> 2 & 1,
        val >> 3 & 1,
        val >> 4 & 1,
        val >> 5 & 1,
        val >> 6 & 1,
        val >> 7 & 1
    ]

class Monome(aiosc.OSCProtocol):
    def __init__(self, prefix='python'):
        self.prefix = prefix.strip('/')
        self.id = None
        self.width = None
        self.height = None
        self.rotation = None

        super().__init__(handlers={
            '/sys/disconnect': lambda *args: self.disconnect,
            #'/sys/connect': lambda *args: self.connect,
            '/sys/{id,size,host,port,prefix,rotation}': self.sys_info,
            '/{}/grid/key'.format(self.prefix): lambda addr, path, x, y, s: self.grid_key(x, y, s),
            '/{}/tilt'.format(self.prefix): lambda addr, path, n, x, y, z: self.tilt(n, x, y, z),
        })

    def connection_made(self, transport):
        super().connection_made(transport)
        self.host, self.port = transport.get_extra_info('sockname')
        self.connect()

    def connect(self):
        self.send('/sys/host', self.host)
        self.send('/sys/port', self.port)
        self.send('/sys/prefix', self.prefix)
        self.send('/sys/info', self.host, self.port)

    def disconnect(self):
        #self.transport.close()
        pass

    def sys_info(self, addr, path, *args):
        if path == '/sys/id':
            self.id = args[0]
        elif path == '/sys/size':
            self.width, self.height = (args[0], args[1])
        elif path == '/sys/rotation':
            self.rotation = args[0]

        # TODO: refine conditions for reinitializing
        # in case rotation, etc. changes
        # Note: arc will report 0, 0 for its size
        if all(x is not None for x in [self.id, self.width, self.height, self.rotation]):
            self.ready()

    def ready(self):
        pass

    def grid_key(self, x, y, s):
        pass

    def tilt(self, n, x, y, z):
        pass

    def led_set(self, x, y, s):
        self.send('/{}/grid/led/set'.format(self.prefix), x, y, s)

    def led_all(self, s):
        self.send('/{}/grid/led/all'.format(self.prefix), s)

    def led_map(self, x_offset, y_offset, data):
        args = [pack_row(data[i]) for i in range(8)]
        self.send('/{}/grid/led/map'.format(self.prefix), x_offset, y_offset, *args)

    def led_row(self, x_offset, y, data):
        args = [pack_row(data[i*8:(i+1)*8]) for i in range(len(data) // 8)]
        self.send('/{}/grid/led/row'.format(self.prefix), x_offset, y, *args)

    def led_col(self, x, y_offset, data):
        args = [pack_row(data[i*8:(i+1)*8]) for i in range(len(data) // 8)]
        self.send('/{}/grid/led/col'.format(self.prefix), x, y_offset, *args)

    def led_intensity(self, i):
        self.send('/{}/grid/led/intensity'.format(self.prefix), i)

    def led_level_set(self, x, y, l):
        self.send('/{}/grid/led/level/set'.format(self.prefix), x, y, l)

    def led_level_all(self, l):
        self.send('/{}/grid/led/level/all'.format(self.prefix), l)

    def led_level_map(self, x_offset, y_offset, data):
        self.send('/{}/grid/led/level/map'.format(self.prefix), x_offset, y_offset, *data)

    def led_level_row(self, x_offset, y, data):
        self.send('/{}/grid/led/level/row'.format(self.prefix), x_offset, y, *data)

    def led_level_col(self, x, y_offset, data):
        self.send('/{}/grid/led/level/col'.format(self.prefix), x, y_offset, *data)

    def tilt_set(self, n, s):
        self.send('/{}/tilt/set'.format(self.prefix), n, s)

class BitBuffer:
    def __init__(self, width, height):
        self.leds = [[0 for col in range(width)] for row in range(height)]
        self.width = width
        self.height = height

    def __and__(self, other):
        result = BitBuffer(self.width, self.height)
        for row in range(self.height):
            for col in range(self.width):
                result.leds[row][col] = self.leds[row][col] & other.leds[row][col]
        return result

    def __xor__(self, other):
        result = BitBuffer(self.width, self.height)
        for row in range(self.height):
            for col in range(self.width):
                result.leds[row][col] = self.leds[row][col] ^ other.leds[row][col]
        return result

    def __or__(self, other):
        result = BitBuffer(self.width, self.height)
        for row in range(self.height):
            for col in range(self.width):
                result.leds[row][col] = self.leds[row][col] | other.leds[row][col]
        return result

    def led_set(self, x, y, s):
        if x < self.width and y < self.height:
            row, col = y, x
            self.leds[row][col] = s

    def led_all(self, s):
        for x in range(self.width):
            for y in range(self.height):
                row, col = y, x
                self.leds[row][col] = s

    def led_map(self, x_offset, y_offset, data):
        for r, row in enumerate(data):
            self.led_row(x_offset, y_offset + r, row)

    def led_row(self, x_offset, y, data):
        for x, s in enumerate(data):
            self.led_set(x_offset + x, y, s)

    def led_col(self, x, y_offset, data):
        for y, s in enumerate(data):
            self.led_set(x, y_offset + y, s)

    def clear(self):
        self.led_all(0)

    def get_map(self, x_offset, y_offset):
        m = []
        for y in range(y_offset, y_offset + 8):
            row = [self.leds[y][col] for col in range(x_offset, x_offset + 8)]
            m.append(row)
        return m

    def render(self, monome):
        for x_offset in [i * 8 for i in range(self.width // 8)]:
            for y_offset in [i * 8 for i in range(self.height // 8)]:
                monome.led_map(x_offset, y_offset, self.get_map(x_offset, y_offset))

class Page:
    def __init__(self, app):
        self.app = app
        self.intensity = 15

    @property
    def buffer(self):
        return self.__buffer

    def ready(self):
        self.__buffer = BitBuffer(self.width, self.height)

    def led_set(self, x, y, s):
        self.__buffer.led_set(x, y, s)
        if self is self.app.current_page:
            self.app.led_set(x, y, s)

    def led_all(self, s):
        self.__buffer.led_all(s)
        if self is self.app.current_page:
            self.app.led_all(s)

    def led_map(self, x_offset, y_offset, data):
        self.__buffer.led_map(x_offset, y_offset, data)
        if self is self.app.current_page:
            self.app.led_map(x_offset, y_offset, data)

    def led_row(self, x_offset, y, data):
        self.__buffer.led_row(x_offset, y, data)
        if self is self.app.current_page:
            self.app.led_row(x_offset, y, data)

    def led_col(self, x, y_offset, data):
        self.__buffer.led_col(x, y_offset, data)
        if self is self.app.current_page:
            self.app.led_col(x, y_offset, data)

    def led_intensity(self, i):
        self.intensity = i
        if self is self.app.current_page:
            self.app.led_intensity(i)

from enum import Enum
class PageCorner(Enum):
    top_left = 1
    top_right = 2
    bottom_left = 3
    bottom_right = 4

class BasePageManager(Monome):
    def __init__(self, pages, prefix='/manager'):
        super().__init__(prefix)
        self.pages = pages
        self.pressed_buttons = set()
        self.current_page = self.pages[0]

    def ready(self):
        super().ready()
        for page in self.pages:
            page.width = self.width
            page.height = self.height
            page.ready()

    def disconnect(self):
        super().disconnect()
        for page in self.pages:
            page.disconnect()

    def grid_key(self, x, y, s):
        if s == 1:
            # remember key-downs so we can up them later
            self.pressed_buttons.add((x, y))
            self.current_page.grid_key(x, y, s)
        else:
            # send key-ups if needed too
            if (x, y) in self.pressed_buttons:
                self.pressed_buttons.remove((x, y))
                self.current_page.grid_key(x, y, s)

    def switch_page(self, page_num):
        # send key-ups to previously active page
        if page_num == -1 or self.pages[page_num] is not self.current_page:
            for x, y in self.pressed_buttons:
                self.current_page.grid_key(x, y, 0)
            self.pressed_buttons.clear()

        if page_num == -1:
            self.current_page = None
            self.led_all(0)
        else:
            # render current page
            self.current_page = self.pages[page_num]
            for x_offset in [i * 8 for i in range(self.width // 8)]:
                for y_offset in [i * 8 for i in range(self.height // 8)]:
                    led_map = self.current_page.buffer.get_map(x_offset, y_offset)
                    self.led_map(0, 0, led_map)

class PageManager(BasePageManager):
    def __init__(self, pages, prefix='/manager', switch=PageCorner.top_right):
        super().__init__(pages, prefix)
        self.switch = switch

    def ready(self):
        super().ready()

        if self.switch == PageCorner.top_left:
            self.switch_button = (0, 0)
        elif self.switch == PageCorner.top_right:
            self.switch_button = (self.width - 1, 0)
        elif self.switch == PageCorner.bottom_left:
            self.switch_button = (0, self.height - 1)
        elif self.switch == PageCorner.bottom_right:
            self.switch_button = (self.width - 1, self.height - 1)
        else:
            raise RuntimeError

    def grid_key(self, x, y, s):
        if (x, y) == self.switch_button:
            if s == 1:
                self.selected_page = self.pages.index(self.current_page)
                self.switch_page(-1)
                self.display_chooser()
            else:
                self.switch_page(self.selected_page)
            return
        # handle regular buttons
        if self.current_page is None:
            if x < len(self.pages):
                self.selected_page = x
                self.display_chooser()
            return
        super().grid_key(x, y, s)

    def display_chooser(self):
        self.led_all(0)
        page_row = [1 if i < len(self.pages) else 0 for i in range(self.width)]
        self.led_row(0, self.height - 1, page_row)
        self.led_col(self.selected_page, 0, [1] * self.height)

class BaseSerialOsc(aiosc.OSCProtocol):
    def __init__(self):
        super().__init__(handlers={
            '/serialosc/device': self.serialosc_device,
            '/serialosc/add': self.serialosc_add,
            '/serialosc/remove': self.serialosc_remove,
        })
        self.devices = {}

    def connection_made(self, transport):
        super().connection_made(transport)
        self.host, self.port = transport.get_extra_info('sockname')

        self.send('/serialosc/list', self.host, self.port)
        self.send('/serialosc/notify', self.host, self.port)

    def device_added(self, id, type, port):
        self.devices[id] = port

    def device_removed(self, id, type, port):
        del self.devices[id]

    def serialosc_device(self, addr, path, id, type, port):
        self.device_added(id, type, port)

    def serialosc_add(self, addr, path, id, type, port):
        self.device_added(id, type, port)
        self.send('/serialosc/notify', self.host, self.port)

    def serialosc_remove(self, addr, path, id, type, port):
        self.device_removed(id, type, port)
        self.send('/serialosc/notify', self.host, self.port)

class SerialOsc(BaseSerialOsc):
    def __init__(self, app_factories, loop=None):
        super().__init__()
        self.app_factories = app_factories
        self.app_instances = {}

        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop

    def device_added(self, id, type, port):
        super().device_added(id, type, port)

        if id in self.app_factories:
            asyncio.async(self.autoconnect(id, self.app_factories[id], port))
        elif '*' in self.app_factories:
            asyncio.async(self.autoconnect(id, self.app_factories['*'], port))

    @asyncio.coroutine
    def autoconnect(self, id, app, port):
        transport, app = yield from self.loop.create_datagram_endpoint(
            app,
            local_addr=('127.0.0.1', 0),
            remote_addr=('127.0.0.1', port)
        )

        apps = self.app_instances.get(id, [])
        apps.append(app)
        self.app_instances[id] = apps

    def device_removed(self, id, type, port):
        super().device_removed(id, type, port)

        if id in self.app_instances:
            self.app_instances[id].disconnect()
            del self.apps[id]

@asyncio.coroutine
def create_serialosc_connection(app_or_apps, loop=None):
    if isinstance(app_or_apps, dict):
        apps = app_or_apps
    else:
        apps = {'*': app_or_apps}

    if loop is None:
        loop = asyncio.get_event_loop()

    transport, serialosc = yield from loop.create_datagram_endpoint(
        lambda: SerialOsc(apps),
        local_addr=('127.0.0.1', 0),
        remote_addr=('127.0.0.1', 12002)
    )
    return serialosc
