========
pymonome
========

pymonome is a pure Python library for easy interaction with the
`monome family <https://monome.org>` of devices. It supports grid and arc
controllers (via serialosc) and provides additional classes for developing
grid- and arc-based applications.

Usage
=====

pymonome does not communicate with any of the devices directly. Like many
monome applications, it uses serialosc for device detection and hardware
input and output. As serialosc provides OSC (UDP) ports for all the devices
connected to the host system, it is possible to connect to a grid via a known
UDP port as follows:

.. code-block:: python

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

In practice, however, UDP ports will be randomly assigned to devices as they
are connected to the host computer. serialosc has a discovery and notification
mechanism to notify clients about connected devices, so we can use this in
pymonome as follows:

.. code-block:: python

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

In the example above, application instance (HelloApp) will be connected
to the latest grid discovered and pressing the button will light the corresponding
LED. For more examples see the ``examples/`` directory.

License
=======

Copyright (c) 2011-2020 Artem Popov <artfwo@gmail.com>

pymonome is licensed under the MIT license, please see LICENSE file for details.
