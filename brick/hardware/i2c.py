from smbus2_asyncio import SMBus2Asyncio


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

    async def setup(self):
        for bus in self.bus.values():
            await bus.open()

i2c_manager = I2CManager()


