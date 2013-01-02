#! /usr/bin/env python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#
# Copyright (C) 2011 Artem Popov <artfwo@gmail.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#

import socket, select, pybonjour, threading, random
from OSC import OSCClient, OSCServer, OSCMessage, NoCallbackError

REGTYPE = '_monome-osc._udp'
DEFAULT_PREFIX = '/python'

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

def find_any_monome():
    browser = MonomeBrowser()
    while len(browser.devices) < 1:
        browser.poll()
    host, port = browser.devices.values()[0]
    browser.close()
    return host, port

def find_monome(serial):
    """
    find a particular monome indicated by the serial number.

    this function blocks until the monome is available.
    """
    browser = MonomeBrowser()
    while not browser.devices.has_key(serial):
        browser.poll()
    host, port = browser.devices[serial]
    browser.close()
    return host, port

def list_monomes():
    """
    list connected monomes.
    """
    browser = MonomeBrowser()
    browser.poll(timeout=0.05)
    return browser.devices


def fix_prefix(s):
    return '/%s' % s.strip('/')

# TODO: unfocus on host 
# TODO: /sys/connect
class Monome(OSCServer):
    def __init__(self, address):
        OSCServer.__init__(self, ('', 0))
        self.client.connect(address)
        host, port = self.client.socket.getsockname()
        
        self.focused = False
        #self.server_host = host
        #self.server_port = port
        self.prefix = DEFAULT_PREFIX
        
        self.addMsgHandler('default', self.monome_handler)
        self.addMsgHandler('/sys/connect', self.sys_misc)
        self.addMsgHandler('/sys/disconnect', self.sys_misc)
        self.addMsgHandler('/sys/id', self.sys_misc)
        self.addMsgHandler('/sys/size', self.sys_size)
        self.addMsgHandler('/sys/host', self.sys_host)
        self.addMsgHandler('/sys/port', self.sys_port)
        self.addMsgHandler('/sys/prefix', self.sys_prefix)
        self.addMsgHandler('/sys/rotation', self.sys_misc)
        
        # handshake
        msg = OSCMessage("/sys/host")
        msg.append(host)
        self.client.send(msg)
        
        msg = OSCMessage("/sys/port")
        msg.append(port)
        self.client.send(msg)
        
        msg = OSCMessage("/sys/info")
        self.client.send(msg)
        
        #self.app_callback = None
    
    def sys_misc(self, *args):
        pass
    
    def sys_host(self, addr, tags, data, client_address):
        pass
    
    def sys_port(self, addr, tags, data, client_address):
        host, port = self.server_address
        if port == data[0]:
            self.focused = True
            self.send('/sys/prefix', self.prefix)
        else:
            self.focused = False
            print "lost focus (device changed port)"
    
    # prefix confirmation
    def sys_prefix(self, addr, tags, data, client_address):
        self.prefix = fix_prefix(data[0])
    
    def sys_size(self, addr, tags, data, client_address):
        self.xsize, self.ysize = data
    
    def send(self, path, *args):
        msg = OSCMessage(path)
        map(msg.append, args)
        self.client.send(msg)
    
    def led_all(self, s):
        self.send("%s%s" % (self.prefix, "/grid/led/all"), s)
    
    def led_set(self, x, y, s):
        self.send("%s%s" % (self.prefix, "/grid/led/set"), x, y, s)
    
    def led_row(self, x, y, *data):
        self.send("%s%s" % (self.prefix, "/grid/led/row"), x, y, *data)
    
    def led_col(self, x, y, *data):
        self.send("%s%s" % (self.prefix, "/grid/led/col"), x, y, *data)
    
    def led_map(self, x, y, data):
        self.send("%s%s" % (self.prefix, "/grid/led/map"), x, y, data)
    
    def led_intensity(self, s):
        self.send("%s%s" % (self.prefix, "/grid/led/intensity"), s)
    
    def monome_handler(self, addr, tags, data, client_address):
        if addr.startswith(self.prefix):
            try:
                method = addr.replace(self.prefix, "", 1).replace("/", "_").strip("_")
                getattr(self, method)(*data)
            except AttributeError:
                pass
        else:
			raise NoCallbackError(addr)
    
    # threading
    def poll(self, timeout=None):
        ready = select.select([self], [], [], timeout)[0]
        for r in ready:
            self.handle_request()
    
    def start(self):
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()
    
    def run(self):
        self.running = True
        while self.running:
            self.poll()
        self.close()
    
    #def close(self):
    #    self.running = False
    #    #self.sdRef.close()

class MonomeBrowser(object):
    def __init__(self):
        self.sdRef = pybonjour.DNSServiceBrowse(regtype=REGTYPE, callBack=self.browse_callback)
        self.resolved = False
        self.devices = {}
    
    def resolve_callback(self, sdRef, flags, interfaceIndex, errorCode, fullname, hosttarget, port, txtRecord):
        if errorCode != pybonjour.kDNSServiceErr_NoError:
            return
        self.resolved = True
        self.resolved_host = hosttarget
        self.resolved_port = port
    
    def browse_callback(self, sdRef, flags, interfaceIndex, errorCode, serviceName, regtype, replyDomain):
        if errorCode != pybonjour.kDNSServiceErr_NoError:
            return

        serial = serviceName.split()[-1].strip('()')

        # FIXME: IPV4 and IPv6 are separate services and are resolved twice
        if not (flags & pybonjour.kDNSServiceFlagsAdd):
            if self.devices.has_key(serial):
                #print "%s removed" % serial
                del self.devices[serial]
            return
        
        resolve_sdRef = pybonjour.DNSServiceResolve(0, interfaceIndex,
            serviceName, regtype, replyDomain, self.resolve_callback)
        
        try:
            while not self.resolved:
                ready = select.select([resolve_sdRef], [], [], 5)
                if resolve_sdRef not in ready[0]:
                    print 'Resolve timed out'
                    break
                pybonjour.DNSServiceProcessResult(resolve_sdRef)
        finally:
            resolve_sdRef.close()
        
        if self.resolved and not self.devices.has_key(serial):
            #print "%s detected" % serial
            self.devices[serial] = (self.resolved_host, self.resolved_port)
        self.resolved = False

    # threading    
    def poll(self, timeout=None):
        ready = select.select([self.sdRef], [], [], timeout)[0]
        for r in ready:
            pybonjour.DNSServiceProcessResult(r)
    
    def start(self):
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()
    
    def run(self):
        self.running = True
        while self.running:
            self.poll()
        self.sdRef.close()
    
    def close(self):
        self.running = False
        #self.sdRef.close()

class LedBuffer(object):
    def __init__(self, xsize, ysize):
        self.leds = bytearray(xsize * ysize >> 3)
        self.xsize = xsize
        self.ysize = ysize
    
    def __and__(self, other):
        result = LedBuffer(self.xsize, self.ysize)
        for i, value in enumerate(self.leds):
            result.leds[i] = value & other.leds[i]
        return result
    
    def __xor__(self, other):
        result = LedBuffer(self.xsize, self.ysize)
        for i, value in enumerate(self.leds):
            result.leds[i] = value ^ other.leds[i]
        return result
    
    def __or__(self, other):
        result = LedBuffer(self.xsize, self.ysize)
        for i, value in enumerate(self.leds):
            result.leds[i] = value | other.leds[i]
        return result
    
    # monome-compatible methods
    def set_led(self, x, y, s):
        q = x / 8 * self.ysize + y
        x = x & 7
        self.leds[q] = (self.leds[q] & ~(1 << x) | (s & 1) << x)
    
    def set_row(self, x, y, s):
        q = x / 8 * self.ysize + y
        self.leds[q] = s
    
    def set_col(self, x, y, s):
        for i, e in enumerate(unpack_row(s)):
            self.set_led(x, y+i, e)
    
    # painting stuff
    def randomize(self):
        for i in range(len(self.leds)):
            self.leds[i] = random.randint(0,0xff)
    
    def fill(self):
        for i in range(len(self.leds)):
            self.leds[i] = 0xff
    
    def clear(self):
        for i in range(len(self.leds)):
            self.leds[i] = 0
    
    def get_led(self, x, y):
        q = x / 8 * self.ysize + y
        x = x & 7
        return self.leds[q] >> x & 1
    
    def get_row(self, x, y):
        q = x / 8 * self.ysize + y
        return unpack_row(self.leds[q])
    
    def get_col(self, x, y):
        return [self.get_led(x, y+i) for i in range(8)]
    
    def get_map(self, x, y):
        q = (x >> 3) + (y >> 3)
        return [
            self.leds[0], self.leds[1], self.leds[2], self.leds[3],
            self.leds[4], self.leds[5], self.leds[6], self.leds[7]
        ]
    
    def pretty_print(self):
        top = '─' * (self.xsize * 2 + 1)
        print("┌" + top + "┐")
        for y in range(self.ysize):
            row = [self.get_led(x, y) for x in range(self.xsize)]
            pretty_row = " ".join(['■' if s == 1 else '▫' for s in row])
            print("│ " + pretty_row + " │")
        print("└" + top + "┘")

