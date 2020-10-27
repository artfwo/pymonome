#! /usr/bin/env python3
#
# Test for a push-button monome arc

import asyncio
import monome

class ExampleArc(monome.Arc):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ExampleArcApp(monome.ArcApp):   
    def __init__(self):
        arc = ExampleArc()
        self.pos = [0, 0, 0, 0];
        super().__init__(arc)
        
    def on_arc_ready(self):
        print('Ready, clearing all rings...')
        for n in range(0,4):
            self.arc.ring_all(n,0)
            
    def on_arc_disconnect(self):
        print('Arc disconnected.')
        
    def on_arc_delta(self, ring, delta):
        print('Ring: {} Delta: {}'.format(ring, delta))
        
        oldPos = self.pos[ring]
        newPos = oldPos + delta
        
        if newPos > oldPos:
            for p in range(oldPos, newPos):
                self.arc.ring_set(ring, p, 15)
        else:
            for p in range(newPos, oldPos):
                self.arc.ring_set(ring, p, 0)
        self.pos[ring] = newPos

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
