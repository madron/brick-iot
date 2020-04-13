import uasyncio as asyncio


class Device:
    async def start(self):
        self.log.debug('Started')
        self._main_task = asyncio.create_task(self._main_loop_wrapper())

    async def stop(self):
        self._main_task.cancel()
        self.log.debug('Stopped')

    async def _main_loop_wrapper(self):
        # Check log and broker
        assert bool(self.log)
        assert bool(self.broker)
        # State
        self._state = dict()
        while True:
            try:
                await self.main_loop()
                self.log.warning('main_loop should run forever')
            except Exception as error:
                self.log.exception('main_loop error', error)
            await asyncio.sleep(10)

    def set_state(self, topic, payload):
        self.log.debug('{} {}'.format(topic, payload))
        self._state[topic] = payload
        self.broker.publish(topic=topic, payload=payload)

    async def main_loop(self):
        while True:
            await asyncio.sleep(10)

    async def message_callback(self, sender=None, topic=None, payload=None):
        pass
