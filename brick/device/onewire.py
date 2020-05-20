import asyncio
import json
from brick.device import Device, NumericSensor, register_device
try:
    from brick.hardware.onewire.w1thermsensor import W1ThermSensor
except:
    pass


@register_device()
class OneWireDetect(Device):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def setup(self):
        sensors = await self.get_sensors()
        self.set_state('sensors', json.dumps(sensors))

    async def get_sensors(self):
        sensors = await W1ThermSensor.get_available_sensors()
        return [dict(id=s.id, type=s.type_name) for s in sensors]


@register_device()
class DS18x20(NumericSensor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def setup(self):
        await super().setup()
        self.sensor = W1ThermSensor()
        await self.sensor.setup()

    async def get_value(self):
        return await self.sensor.get_temperature()
