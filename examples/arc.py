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
        print('Ring: {} Delta: {}'.format(ring, delta))
        
        old_pos = self.pos[ring]
        new_pos = old_pos + delta
        
        if new_pos > old_pos:
            for p in range(old_pos, new_pos):
                self.arc.ring_set(ring, p, 15)
        else:
            for p in range(new_pos, old_pos):
                self.arc.ring_set(ring, p, 0)
        self.pos[ring] = new_pos

    def on_arc_key(self, ring, s):
        print('Ring: {} Pressed:{}'.format(ring, s > 0))
        self.arc.ring_all(ring, 15 if s > 0 else 0)
        

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    app = ExampleArcApp()

    def serialosc_device_added(id, type, port):
        print('connecting to {} ({})'.format(id, type))
        asyncio.ensure_future(app.arc.connect('127.0.0.1', port))

    serialosc = monome.SerialOsc()
    serialosc.device_added_event.add_handler(serialosc_device_added)

    loop.run_until_complete(serialosc.connect())

    loop.run_forever()
