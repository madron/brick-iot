class Component:
    async def clean_config(self, config=dict()):
        raise NotImplementedError()

    async def start(self):
        raise NotImplementedError()

    async def stop(self):
        raise NotImplementedError()


class FakeComponent(Component):
    async def start(self):
        pass

    async def stop(self):
        pass
