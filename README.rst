========
pymonome
========

pymonome is a pure Python library for easy interaction with the
`monome family <https://monome.org>` of devices. It supports grid and arc
controllers (via serialosc) and provides additional facilities for developing
grid- and arc-based applications.

Installation
============

pymonome requires at least Python 3.6. It can be installed using pip::

    pip3 install pymonome

Or use the ``--user`` option to install pymonome to the current user
library directory::

    pip3 install --user pymonome

Basic usage
===========

pymonome does not communicate with any of the devices directly. Like many
monome applications, it relies on serialosc for device detection and hardware
input and output. As serialosc provides OSC (UDP) ports for all the devices
connected to the host system, it is possible to connect to a grid via a known
UDP port as follows:

.. code-block:: python

    import monome

    GRID_HOST = '127.0.0.1'
    GRID_PORT = 16816

    grid = monome.Grid()
    await grid.connect(GRID_HOST, GRID_PORT)
    grid.led_set(0, 0, 1)

Alternatively, it is possible to instantiate the protocol class using the
``loop.create_datagram_endpoint()`` event loop method:

.. code-block:: python

    transport, grid = await loop.create_datagram_endpoint(monome.Grid,
        remote_addr=(GRID_HOST, GRID_PORT))

Service discovery API
=====================

In practice UDP ports will be randomly assigned to devices as they
are connected to the host computer. serialosc has a discovery and
notification mechanism to notify clients about connected devices.
It's possible to connect to the discovery service from pymonome too:

.. code-block:: python

    grid = monome.Grid()

    def serialosc_device_added(id, type, port):
        print('connecting to {} ({})'.format(id, type))
        asyncio.create_task(grid.connect('127.0.0.1', port))

    serialosc = monome.SerialOsc()
    serialosc.device_added_event.add_handler(serialosc_device_added)

    await serialosc.connect()

Application classes
===================

For extra convenience pymonome provides base classes for developing
grid and arc-based apps, apps on grid sections, or pages on the same grid.
Application base classes provide handler stubs for input events
and member properties for accessing controllers.

.. code-block:: python

    import asyncio
    import monome

    class HelloApp(monome.GridApp):
        def on_grid_key(self, x, y, s):
            self.grid.led_set(x, y, s)

    async def main():
        loop = asyncio.get_running_loop()
        hello_app = HelloApp()

        def serialosc_device_added(id, type, port):
            print('connecting to {} ({})'.format(id, type))
            asyncio.create_task(hello_app.grid.connect('127.0.0.1', port))

        serialosc = monome.SerialOsc()
        serialosc.device_added_event.add_handler(serialosc_device_added)

        await serialosc.connect()
        await loop.create_future() # run forever

    if __name__ == '__main__':
        asyncio.run(main())

In this example, HelloApp application instance will be connected
to the latest discovered grid and pressing a button will light
the corresponding LED.

More examples
=============

For more examples see the ``examples/`` directory.

License
=======

Copyright (c) 2011-2021 Artem Popov <artfwo@gmail.com>

pymonome is licensed under the MIT license, please see LICENSE file for details.
