from brick.device.base import Device
import random
import uasyncio as asyncio


class Random(Device):
    def __init__(self, delay=10, scale=100):
        self.delay = int(delay)
        self.scale = int(scale)

    async def main_loop(self):
        while True:
            self.set_state('value',  random.randint(0, self.scale))
            await asyncio.sleep(self.delay)
