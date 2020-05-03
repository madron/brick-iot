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
        return await W1ThermSensor.get_available_sensors()
