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
import re


DISCONNECTED, CONNECTING, READY = range(3)

def pack_row(row):
    return row[7] << 7 | row[6] << 6 | row[5] << 5 | row[4] << 4 | row[3] << 3 | row[2] << 2 | row[1] << 1 | row[0]


class Grid(aiosc.OSCProtocol):
    def __init__(self):
        self.prefix = 'monome'
        self.id = None
        self.width = None
        self.height = None
        self.varibright = True
        self.state = DISCONNECTED

        super().__init__(handlers={
            '/sys/connect': lambda *args: self.__sys_connect(),
            '/sys/disconnect': lambda *args: self.__sys_disconnect(),
            '/sys/{id,size,host,port,prefix,rotation}': self.__sys_info,
            '/*/grid/key'.format(self.prefix): self.__grid_key,
            '/*/tilt'.format(self.prefix): self.__tilt,
        })

        self.event_handler = None

    def connection_made(self, transport):
        super().connection_made(transport)
        self.host, self.port = transport.get_extra_info('sockname')

    def connect(self):
        if self.state == DISCONNECTED:
            self.state = CONNECTING
            self.send('/sys/host', self.host)
            self.send('/sys/port', self.port)
            self.send('/sys/prefix', self.prefix)
            #self.send('/sys/info', self.host, self.port)
            self.send('/sys/info/id', self.host, self.port)
            self.send('/sys/info/size', self.host, self.port)

    def __sys_connect(self):
        # TODO: shouldn't normally happen, because we close the socket on disconnect
        pass

    def __sys_disconnect(self):
        self.state = DISCONNECTED
        self.transport.close()

        if self.event_handler is not None:
            self.event_handler.on_grid_disconnect()

    def __sys_info(self, addr, path, *args):
        if path == '/sys/id':
            self.id = args[0]
        elif path == '/sys/size':
            self.width, self.height = (args[0], args[1])
        elif path == '/sys/rotation':
            self.rotation = args[0]

        if all(x is not None for x in [self.id, self.width, self.height]):
            self.state = READY

            if not re.match('^m\d+$', self.id):
                self.varibright = False

            self.__ready()

    def __ready(self):
        if self.event_handler is not None:
            self.event_handler.on_grid_ready()

    def __grid_key(self, addr, path, x, y, s):
        if self.event_handler is not None and path.startswith("/" + self.prefix):
            self.event_handler.on_grid_key(x, y, s)

    def __tilt(self, addr, path, n, x, y, z):
        if self.event_handler is not None and path.startswith("/" + self.prefix):
            self.event_handler_on_tilt(n, x, y, z)

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


class GridWrapper:
    def __init__(self, grid):
        self.grid = grid
        self.grid.event_handler = self
        self.event_handler = None

    def connect(self):
        if self.grid.state == DISCONNECTED:
            self.grid.connect()
        elif self.grid.state == CONNECTED:
            self.on_grid_ready()

    def on_grid_ready(self):
        self.width = self.grid.width
        self.height = self.grid.height
        self.event_handler.on_grid_ready()

    def on_grid_key(self, x, y, s):
        self.event_handler.on_grid_key(x, y, s)

    def on_grid_disconnect(self):
        self.event_handler.on_grid_disconnect()

    def led_set(self, x, y, s):
        self.grid.led_set(x, y, s)

    def led_all(self, s):
        self.grid.led_all(s)

    def led_map(self, x_offset, y_offset, data):
        self.grid.led_map(x_offset, y_offset, data)

    def led_row(self, x_offset, y, data):
        self.grid.led_row(x_offset, y, data)

    def led_col(self, x, y_offset, data):
        self.grid.led_col(x, y_offset, data)

    def led_intensity(self, i):
        self.grid.led_intensity(i)

    def led_level_set(self, x, y, l):
        self.grid.led_level_set(x, y, l)

    def led_level_all(self, l):
        self.grid.led_level_all(l)

    def led_level_map(self, x_offset, y_offset, data):
        self.grid.led_level_map(x_offset, y_offset, data)

    def led_level_row(self, x_offset, y, data):
        self.grid.led_level_row(x_offset, y, data)

    def led_level_col(self, x, y_offset, data):
        self.grid.led_level_col(x, y_offset, data)

    def tilt_set(self, n, s):
        self.grid.tilt_set(n, s)


class GridBuffer:
    def __init__(self, width, height):
        self.levels = [[0 for col in range(width)] for row in range(height)]
        self.width = width
        self.height = height

    def __and__(self, other):
        result = GridBuffer(self.width, self.height)
        for row in range(self.height):
            for col in range(self.width):
                result.levels[row][col] = self.levels[row][col] & other.levels[row][col]
        return result

    def __xor__(self, other):
        result = GridBuffer(self.width, self.height)
        for row in range(self.height):
            for col in range(self.width):
                result.levels[row][col] = self.levels[row][col] ^ other.levels[row][col]
        return result

    def __or__(self, other):
        result = GridBuffer(self.width, self.height)
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
            for y, l in enumerate(data[:self.height - y_offset]):
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

    def render(self, grid):
        for x_offset in [i * 8 for i in range(self.width // 8)]:
            for y_offset in [i * 8 for i in range(self.height // 8)]:
                grid.led_level_map(x_offset, y_offset, self.get_level_map(x_offset, y_offset))


class Page:
    def __init__(self):
        self.manager = None
        self.__buffer = None

    @property
    def buffer(self):
        return self.__buffer

    def on_grid_ready(self):
        self.__buffer = GridBuffer(self.width, self.height)
        self.event_handler.on_grid_ready()

    def on_grid_key(self, x, y, s):
        self.event_handler.on_grid_key(x, y, s)

    def on_grid_disconnect(self):
        self.event_handler.on_grid_disconnect()

    def is_active(self):
        return self is self.manager.current_page

    def connect(self):
        pass # TODO: not needed?

    def render(self):
        self.__buffer.render(self.manager)

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
        self.manager.led_intensity(i)

    def led_level_set(self, x, y, l):
        self.__buffer.led_level_set(x, y, l)
        if self.is_active():
            self.manager.led_level_set(x, y, l)

    def led_level_all(self, l):
        self.__buffer.led_level_all(l)
        if self.is_active():
            self.manager.led_level_all(l)

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


class BasePageManager(GridWrapper):
    def __init__(self, grid, pages):
        super().__init__(grid)
        self.pages = pages
        for page in self.pages:
            page.manager = self
        self.set_page(0)

    def on_grid_ready(self):
        for page in self.pages:
            page.width = self.grid.width
            page.height = self.grid.height
            page.on_grid_ready()

    def disconnect(self):
        super().disconnect()
        for page in self.pages:
            page.disconnect()

    def on_grid_key(self, x, y, s):
        self.current_page.on_grid_key(x, y, s)

    def set_page(self, index):
        self.current_page = self.pages[index]
        if (self.current_page.buffer):
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
    def __init__(self, grid, pages, switch_button=(-1, -1)):
        super().__init__(grid, pages)
        self.switch_button = switch_button

    def on_grid_ready(self):
        super().on_grid_ready()
        switch_x, switch_y = self.switch_button

        self.switch_x = self.grid.width + switch_x if switch_x < 0 else switch_x
        self.switch_y = self.grid.height + switch_y if switch_y < 0 else switch_y

    def on_grid_key(self, x, y, s):
        # TODO: bring back presses from pymonome 0.8
        if x == self.switch_x and y == self.switch_y and s == 1:
            self.set_page((self.pages.index(self.current_page) + 1) % len(self.pages))
        else:
            super().on_grid_key(x, y, s)

class GridSection:
    def __init__(self, size, offset):
        self.splitter = None
        self.event_handler = None

        self.section_width = size[0]
        self.section_height = size[1]
        self.x_offset = offset[0]
        self.y_offset = offset[1]

    def connect(self):
        pass

    def on_grid_ready(self):
        self.width = self.section_width
        self.height = self.section_height
        self.event_handler.on_grid_ready()

    def on_grid_key(self, x, y, s):
        self.event_handler.on_grid_key(x, y, s)

    def on_grid_disconnect(self):
        self.event_handler.on_grid_disconnect()

    def led_set(self, x, y, s):
        if x < self.section_width and y < self.section_height:
            self.splitter.led_set(x + self.x_offset, y + self.y_offset, s)

    def led_all(self, s):
        # TODO: fix map
        data = [[s for col in range(8)] for row in range(8)]
        self.splitter.led_map(self.x_offset, self.y_offset, data)

    def led_map(self, x_offset, y_offset, data):
        self.splitter.led_map(self.x_offset + x_offset, self.y_offset + y_offset, data)

    def led_row(self, x_offset, y, data):
        data = data[:self.section_width]
        self.splitter.led_row(self.x_offset + x_offset, self.y_offset + y, data)

    def led_col(self, x, y_offset, data):
        data = data[:self.section_height]
        self.splitter.led_col(self.x_offset + x, self.y_offset + y_offset, data)

    def led_intensity(self, i):
        self.splitter.led_intensity(i)

    def led_level_set(self, x, y, l):
        if x < self.section_width and y < self.section_height:
            self.splitter.led_level_set(self.x_offset + x, self.y_offset + y, l)

    def led_level_all(self, l):
        data = [[l for col in range(8)] for row in range(8)]
        self.splitter.led_map(self.x_offset, self.y_offset, data)

    def led_level_map(self, x_offset, y_offset, data):
        self.splitter.led_level_map(self.x_offset + x_offset, self.y_offset + y_offset, data)

    def led_level_row(self, x_offset, y, data):
        data = data[:self.section_width]
        self.splitter.led_level_row(self.x_offset + x_offset, self.y_offset + y, data)

    def led_level_col(self, x, y_offset, data):
        data = data[:self.section_height]
        self.splitter.led_level_col(self.x_offset + x, self.y_offset + y_offset, data)


class Splitter(GridWrapper):
    def __init__(self, grid, sections):
        super().__init__(grid)
        self.sections = sections
        for section in self.sections:
            section.splitter = self

    def on_grid_ready(self):
        for section in self.sections:
            section.on_grid_ready()

    def on_grid_disconnect(self):
        for section in self.sections:
            section.on_grid_disconnect()

    def on_grid_key(self, x, y, s):
        for section in self.sections:
            if section.x_offset <= x < section.x_offset + section.section_width and \
               section.y_offset <= y < section.y_offset + section.section_height:
                section.on_grid_key(x - section.x_offset, y - section.y_offset, s)


class SerialOsc(aiosc.OSCProtocol):
    def __init__(self, loop=None, autoconnect_app=None):
        super().__init__(handlers={
            '/serialosc/device': self.__on_serialosc_device,
            '/serialosc/add': self.__on_serialosc_add,
            '/serialosc/remove': self.__on_serialosc_remove,
        })

        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop

        self.autoconnect_app = autoconnect_app

    @classmethod
    async def create(cls, loop=None, autoconnect_app=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()

        transport, protocol = await loop.create_datagram_endpoint(lambda: cls(loop=loop, autoconnect_app=autoconnect_app, **kwargs),
            local_addr=('127.0.0.1', 0), remote_addr=('127.0.0.1', 12002))
        return protocol

    def connection_made(self, transport):
        super().connection_made(transport)
        self.host, self.port = transport.get_extra_info('sockname')

        self.send('/serialosc/list', self.host, self.port)
        self.send('/serialosc/notify', self.host, self.port)

    def __on_serialosc_device(self, addr, path, id, type, port):
        self.on_device_added(id, type, port)

    def __on_serialosc_add(self, addr, path, id, type, port):
        self.on_device_added(id, type, port)
        self.send('/serialosc/notify', self.host, self.port)

    def __on_serialosc_remove(self, addr, path, id, type, port):
        self.on_device_removed(id, type, port)
        self.send('/serialosc/notify', self.host, self.port)

    def on_device_added(self, id, type, port):
        if self.autoconnect_app is not None:
            asyncio.async(self.autoconnect(self.autoconnect_app, port))

    def on_device_removed(self, id, type, port):
        pass

    async def autoconnect(self, app, grid_port):
        transport, grid = await self.loop.create_datagram_endpoint(Grid,
            local_addr=('127.0.0.1', 0), remote_addr=('127.0.0.1', grid_port))

        app.attach(grid)

class App:
    def __init__(self, prefix='/monome'):
        self.prefix = prefix.strip('/')
        self.grid = None

    def attach(self, grid):
        # TODO: should this happen before or after we connect?
        self.grid = grid
        self.grid.event_handler = self
        self.grid.prefix = self.prefix
        self.grid.connect()

    def detach(self):
        self.grid.event_handler = None
        self.grid = None

    def on_grid_ready(self):
        pass

    def on_grid_disconnect(self):
        self.detach()

    def on_grid_key(self, x, y, s):
        pass
