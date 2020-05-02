import asyncio
from smbus2_asyncio import SMBus2Asyncio
from brick.device import Device, register_device


class I2CManager:
    def __init__(self):
        self.bus = dict()

    def get_bus(self, i2c_bus=0):
        i2c_bus = int(i2c_bus)
        if i2c_bus in self.bus:
            return self.bus[i2c_bus]
        else:
            self.bus[i2c_bus] = SMBus2Asyncio(i2c_bus)
            return self.bus[i2c_bus]


i2c_manager = I2CManager()


@register_device()
class I2CDetect(Device):
    def __init__(self, i2c_bus=0):
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
