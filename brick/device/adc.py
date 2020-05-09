from brick.device import NumericSensor, register_device
from brick.hardware.i2c import i2c_manager
from brick.hardware.ti import ads1x15


@register_device()
class ADS1115(NumericSensor):
    def __init__(self, channel=0, address=0x48, i2c_bus=0, **kwargs):
        super().__init__(**kwargs)
        assert channel in (0, 1, 2 , 3)
        self.channel = channel
        self.voltage_conversion_factor = 4.096 / 32768
        self.bus = i2c_manager.get_bus(i2c_bus)
        self.adc = ads1x15.ADS1115(self.bus, address=address)

    async def setup(self):
        await super().setup()
        await self.bus.open()

    async def get_value(self):
        value = await self.adc.read_adc(self.channel)
        return value * self.voltage_conversion_factor
