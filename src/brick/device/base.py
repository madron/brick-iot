import uasyncio as asyncio


class Device:
    async def start(self):
        self.log.debug('Started')
        await self._setup()
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        await self._teardown()
        self._task.cancel()
        self.log.debug('Stopped')

    async def _setup(self):
        # Check log and broker
        assert bool(self.log)
        assert bool(self.broker)
        # State
        self._state = dict()
        self._subscriptions = dict()
        await self.setup()

    async def _teardown(self):
        await self.teardown()
        for sender, topic in self._subscriptions.keys():
            self.broker.unsubscribe(sender, topic)
        self._subscriptions = dict()

    async def _loop(self):
        while True:
            try:
                await self.loop()
                self.log.warning('loop should run forever')
            except Exception as error:
                self.log.exception('loop error', error)
            await asyncio.sleep(10)

    async def publish_state(self, **kwargs):
        self.log.debug('publish_state')
        for topic, payload in self._state.items():
            self.broker.publish(topic=topic, payload=payload)

    def set_state(self, topic, payload):
        self.log.debug('{} {}'.format(topic, payload))
        self._state[topic] = payload
        self.broker.publish(topic=topic, payload=payload)

    def subscribe(self, callback, sender=None, topic=None):
        self.broker.subscribe(callback, sender=sender, topic=topic)
        self._subscriptions[(sender, topic)] = callback

    async def setup(self):
        pass

    async def teardown(self):
        pass

    async def loop(self):
        while True:
            await asyncio.sleep(10)

    async def message_callback(self, sender=None, topic=None, payload=None):
        pass
