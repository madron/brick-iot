from brick.device import Device, register_device
import random
import uasyncio as asyncio


@register_device()
class Random(Device):
    def __init__(self, delay=10, scale=100):
        self.delay = int(delay)
        self.scale = int(scale)

    async def setup(self):
        self.set_state('delay', self.delay)

    async def loop(self):
        while True:
            self.set_state('value',  random.randint(0, self.scale))
            await asyncio.sleep(self.delay)

    async def message_received(self, sender=None, topic=None, payload=None):
        if topic == 'delay':
            self.delay = int(payload)
            self.set_state('delay', self.delay)
