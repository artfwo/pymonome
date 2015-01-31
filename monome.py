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

import asyncio
import aiosc
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
        val >> 7 & 1,
    ]


class Monome(aiosc.OSCProtocol):
    def __init__(self, prefix='/python', varibright=True):
        self.prefix = prefix.strip('/')
        self.id = None
        self.width = None
        self.height = None
        self.rotation = None
        self.varibright = varibright

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
        if self.varibright:
            self.send('/{}/grid/led/level/set'.format(self.prefix), x, y, l)
        else:
            self.led_set(x, y, l >> 3 & 1)

    def led_level_all(self, l):
        if self.varibright:
            self.send('/{}/grid/led/level/all'.format(self.prefix), l)
        else:
            self.led_all(l >> 3 & 1)

    def led_level_map(self, x_offset, y_offset, data):
        if self.varibright:
            args = itertools.chain(*data)
            self.send('/{}/grid/led/level/map'.format(self.prefix), x_offset, y_offset, *args)
        else:
            self.led_map(x_offset, y_offset, [[l >> 3 & 1 for l in row] for row in data])

    def led_level_row(self, x_offset, y, data):
        if self.varibright:
            self.send('/{}/grid/led/level/row'.format(self.prefix), x_offset, y, *data)
        else:
            self.led_row(x_offset, y, [l >> 3 & 1 for l in data])

    def led_level_col(self, x, y_offset, data):
        if self.varibright:
            self.send('/{}/grid/led/level/col'.format(self.prefix), x, y_offset, *data)
        else:
            self.led_col(x, y_offset, [l >> 3 & 1 for l in data])

    def tilt_set(self, n, s):
        self.send('/{}/tilt/set'.format(self.prefix), n, s)


class LedBuffer:
    def __init__(self, width, height):
        self.levels = [[0 for col in range(width)] for row in range(height)]
        self.width = width
        self.height = height

    def __and__(self, other):
        result = LedBuffer(self.width, self.height)
        for row in range(self.height):
            for col in range(self.width):
                result.levels[row][col] = self.levels[row][col] & other.levels[row][col]
        return result

    def __xor__(self, other):
        result = LedBuffer(self.width, self.height)
        for row in range(self.height):
            for col in range(self.width):
                result.levels[row][col] = self.levels[row][col] ^ other.levels[row][col]
        return result

    def __or__(self, other):
        result = LedBuffer(self.width, self.height)
        for row in range(self.height):
            for col in range(self.width):
                result.levels[row][col] = self.levels[row][col] | other.levels[row][col]
        return result

    def led_set(self, x, y, s):
        self.led_level_set(x, y, s * 15)

    def led_all(self, s):
        self.led_level_all(s * 15)

    def led_map(self, x_offset, y_offset, data):
        for r, row in enumerate(data):
            self.led_row(x_offset, y_offset + r, row)

    def led_row(self, x_offset, y, data):
        for x, s in enumerate(data):
            self.led_set(x_offset + x, y, s)

    def led_col(self, x, y_offset, data):
        for y, s in enumerate(data):
            self.led_set(x, y_offset + y, s)

    def led_level_set(self, x, y, l):
        if x < self.width and y < self.height:
            self.levels[y][x] = l

    def led_level_all(self, l):
        for x in range(self.width):
            for y in range(self.height):
                self.levels[y][x] = l

    def led_level_map(self, x_offset, y_offset, data):
        for r, row in enumerate(data):
            self.led_level_row(x_offset, y_offset + r, row)

    def led_level_row(self, x_offset, y, data):
        if y < self.height:
            for x, l in enumerate(data[:self.width - x_offset]):
                self.levels[y][x + x_offset] = l

    def led_level_col(self, x, y_offset, data):
        if x < self.width:
            for y, s in enumerate(data[:self.height - y_offset]):
                self.levels[y + y_offset][x] = l

    def get_level_map(self, x_offset, y_offset):
        map = []
        for y in range(y_offset, y_offset + 8):
            row = [self.levels[y][col] for col in range(x_offset, x_offset + 8)]
            map.append(row)
        return map

    def get_binary_map(self, x_offset, y_offset):
        map = []
        for y in range(y_offset, y_offset + 8):
            row = [1 if self.levels[y][col] > 7 else 0 for col in range(x_offset, x_offset + 8)]
            map.append(row)
        return map

    def render(self, monome):
        for x_offset in [i * 8 for i in range(self.width // 8)]:
            for y_offset in [i * 8 for i in range(self.height // 8)]:
                monome.led_level_map(x_offset, y_offset, self.get_level_map(x_offset, y_offset))


class Page:
    def __init__(self, manager):
        self.manager = manager
        self.__buffer = None
        self.__intensity = 15

    @property
    def buffer(self):
        return self.__buffer

    def ready(self):
        self.__buffer = LedBuffer(self.width, self.height)

    def is_active(self):
        return self is self.manager.current_page

    # virtual pages shouldn't define stubs so they don't get
    # in place of actual handlers with multiple inheritance
    #def grid_key(self, x, y, s):
    #    pass

    #def disconnect(self):
    #    pass

    def led_set(self, x, y, s):
        self.__buffer.led_set(x, y, s)
        if self.is_active():
            self.manager.led_set(x, y, s)

    def led_all(self, s):
        self.__buffer.led_all(s)
        if self.is_active():
            self.manager.led_all(s)

    def led_map(self, x_offset, y_offset, data):
        self.__buffer.led_map(x_offset, y_offset, data)
        if self.is_active():
            self.manager.led_map(x_offset, y_offset, data)

    def led_row(self, x_offset, y, data):
        self.__buffer.led_row(x_offset, y, data)
        if self.is_active():
            self.manager.led_row(x_offset, y, data)

    def led_col(self, x, y_offset, data):
        self.__buffer.led_col(x, y_offset, data)
        if self.is_active():
            self.manager.led_col(x, y_offset, data)

    def led_intensity(self, i):
        self.__intensity = i
        if self.is_active():
            self.manager.led_intensity(i)

    def led_level_set(self, x, y, l):
        self.__buffer.led_level_set(x, y, l)
        if self.is_active():
            self.manager.led_level_set(x, y, l)

    def led_level_all(self, x, y, l):
        self.__buffer.led_level_all(x, y, l)
        if self.is_active():
            self.manager.led_level_all(x, y, l)

    def led_level_map(self, x_offset, y_offset, data):
        self.__buffer.led_level_map(x_offset, y_offset, data)
        if self.is_active():
            self.manager.led_level_map(x_offset, y_offset, data)

    def led_level_row(self, x_offset, y, data):
        self.__buffer.led_level_row(x_offset, y, data)
        if self.is_active():
            self.manager.led_level_row(x_offset, y, data)

    def led_level_col(self, x, y_offset, data):
        self.__buffer.led_level_col(x, y_offset, data)
        if self.is_active():
            self.manager.led_level_col(x, y_offset, data)

    def render(self):
        self.__buffer.render(self.manager)
        self.manager.led_intensity(self.__intensity)

class BasePageManager(Monome):
    def __init__(self, pages, **kwargs):
        super().__init__(**kwargs)
        self.pages = pages
        self._presses = set()
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
            self._presses.add((x, y))
        else:
            self._presses.discard((x, y))

        self.current_page.grid_key(x, y, s)

    def switch_page(self, page_num):
        # send key-ups to previously active page
        if page_num == -1 or self.pages[page_num] is not self.current_page:
            for x, y in self._presses:
                self.current_page.grid_key(x, y, 0)
            self._presses.clear()

        if page_num == -1:
            self.current_page = None
            self.led_all(0)
        else:
            # render current page
            self.current_page = self.pages[page_num]
            self.current_page.render()

class SumPageManager(BasePageManager):
    def __init__(self, pages, switch_button=(-1, -1), **kwargs):
        super().__init__(pages, **kwargs)
        self.switch_button = switch_button

    def ready(self):
        super().ready()
        switch_x, switch_y = self.switch_button

        self.switch_x = self.width + switch_x if switch_x < 0 else switch_x
        self.switch_y = self.height + switch_y if switch_y < 0 else switch_y

    def grid_key(self, x, y, s):
        if not self._presses and \
           x == self.switch_x and \
           y == self.switch_y:
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

class SeqPageManager(BasePageManager):
    def __init__(self, pages, switch_button=(-1, -1), **kwargs):
        super().__init__(pages, **kwargs)
        self.switch_button = switch_button

    def ready(self):
        super().ready()
        switch_x, switch_y = self.switch_button

        self.switch_x = self.width + switch_x if switch_x < 0 else switch_x
        self.switch_y = self.height + switch_y if switch_y < 0 else switch_y

    def grid_key(self, x, y, s):
        if not self._presses and \
           x == self.switch_x and \
           y == self.switch_y and \
           s == 1:
            self.switch_page((self.pages.index(self.current_page) + 1) % len(self.pages))
        else:
            super().grid_key(x, y, s)


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
            for app in self.app_instances[id]:
                app.disconnect()
            del self.app_instances[id]


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
