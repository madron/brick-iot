import asyncio
import json
from brick.device import Device, register_device
from brick.hardware.onewire.w1thermsensor import W1ThermSensor


@register_device()
class OneWireDetect(Device):
    async def setup(self):
        sensors = await self.get_sensors()
        self.set_state('sensors', json.dumps(sensors))

    async def get_sensors(self):
        sensors = await W1ThermSensor.get_available_sensors()
        return [dict(id=s.id, type=s.type_name) for s in sensors]


@register_device()
class DS18x20(Device):
    def __init__(self, delay=10):
        self.delay = int(delay)

    async def setup(self):
        self.sensor = W1ThermSensor()
        await self.sensor.setup()

    async def loop(self):
        while True:
            self.set_state('temperature', await self.sensor.get_temperature())
            await asyncio.sleep(self.delay)
