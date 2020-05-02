import asyncio
import gpiozero
import smbus
from brick.device import Device, register_device
from brick.device.i2c import i2c_manager
from brick.hardware.ti import ads1x15


@register_device()
class Ads1115(Device):
    def __init__(
        self,
        channel=0,
        delay=10,
        conversion_factor=1,
        config_mode=False,
        address=0x48,
        i2c_bus=0,
    ):
        assert channel in (0, 1, 2 , 3)
        self.channel = channel
        self.delay = int(delay)
        self.conversion_factor = float(conversion_factor)
        self.config_mode = bool(config_mode)
        self.voltage_conversion_factor = 4.096 / 32768
        self.bus = i2c_manager.get_bus(i2c_bus)
        self.adc = ads1x15.ADS1115(self.bus, address=address)

    async def setup(self):
        self.set_state('delay', self.delay)
        self.set_state('conversion_factor', self.conversion_factor)
        await self.bus.open()

    async def loop(self):
        while True:
            value = await self.adc.read_adc(self.channel)
            value = round(value * self.voltage_conversion_factor * self.conversion_factor, 6)
            self.set_state('value', value)
            await asyncio.sleep(self.delay)

    async def message_received(self, sender=None, topic=None, payload=None):
        if self.config_mode:
            if topic == 'delay':
                self.delay = int(payload)
                self.set_state('delay', self.delay)
            if topic == 'conversion_factor':
                self.conversion_factor = float(payload)
                self.set_state('conversion_factor', self.conversion_factor)
