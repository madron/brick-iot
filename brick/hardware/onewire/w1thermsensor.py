import asyncio
import functools
from w1thermsensor import W1ThermSensor as W1ThermSensorSync


class W1ThermSensor(W1ThermSensorSync):
    def __init__(self, loop=None, executor=None):
        self.loop = loop or asyncio.get_event_loop()
        self.executor = executor

    @classmethod
    async def get_available_sensors(cls, types=None, loop=None, executor=None):
        loop = loop or asyncio.get_event_loop()
        sensors = await loop.run_in_executor(
            executor,
            functools.partial(W1ThermSensorSync.get_available_sensors, types=types),
        )
        return [dict(id=s.id, type=s.type_name) for s in sensors]
