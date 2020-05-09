class DigitalInput:
    def __init__(self, device=None, name='', delay=200):
        self.device = device
        self.name = name
        self.delay = delay

    async def setup(self):
        pass

    async def is_pressed(self):
        state = await self.get_state()
        return True if state == 'on' else False

    async def get_state(self):
        raise NotImplementedError()


class DigitalOutput:
    def __init__(self, device=None, name=''):
        self.device = device
        self.name = name

    async def setup(self):
        pass

    async def on(self):
        await self.set_state('on')

    async def off(self):
        await self.set_state('off')

    async def set_state(self, state):
        raise NotImplementedError()
