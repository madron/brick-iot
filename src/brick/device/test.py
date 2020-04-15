from brick.device.base import Device
import random
import uasyncio as asyncio


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


class StatePublish(Device):
    def __init__(self, delay=10):
        self.delay = int(delay)

    async def setup(self):
        self.subscribe(self.log_state)

    async def log_state(self, sender=None, topic=None, payload=None):
        self.log.debug('{}/{} {}'.format(sender, topic, payload))

    async def loop(self):
        while True:
            self.broker.publish(topic='publish_state')
            await asyncio.sleep(self.delay)
