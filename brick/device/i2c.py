import asyncio
from smbus2_asyncio import SMBus2Asyncio
from brick.device import Device, register_device
from brick.hardware.i2c import i2c_manager


@register_device()
class I2CDetect(Device):
    def __init__(self, i2c_bus=0, **kwargs):
        super().__init__(**kwargs)
        self.bus = i2c_manager.get_bus(i2c_bus)
        self.addresses = []

    async def setup(self):
        await self.bus.open()
        addresses = await self.get_addresses()
        self.set_state('adresses', str(addresses))

    async def get_addresses(self):
        addresses = []
        for address in range(128):
            try:
                await self.bus.read_byte_data(address, 0)
                addresses.append(address)
            except:
                pass
        return addresses
