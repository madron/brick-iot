import asyncio
from copy import copy
from time import time_ns
from brick.exceptions import ValidationError
from brick.hardware import Hardware, register_hardware
from brick.hardware.i2c import i2c_manager
from brick.hardware.base import DigitalInput, DigitalOutput
from brick.hardware.mcp import mcp230xx


MCP230XX_DEFAULT_ADDRESS = 0x20
MCP23017_DIRECTION_REGISTER = dict(a=0x00, b=0x01)  # bit 1=in 0=out
MCP23017_PULL_UP_REGISTER = dict(a=0x0C, b=0x0D)  # bit 1 -> pup 100k
MCP23017_GPIO_REGISTER = dict(a=0x12, b=0x13)


class MCP23017Input(DigitalInput):
    def __init__(self, port=None, channel=None, **kwargs):
        super().__init__(**kwargs)
        self.port = port
        self.channel = channel
        self.device.channel_config(port, channel, name=self.name, direction='in')

    async def get_state(self):
        return await self.device.get_channel_state(self.port, self.channel, delay=self.delay)

    async def setup(self):
        await super().setup()
        await self.device.setup()


class MCP23017Output(DigitalOutput):
    def __init__(self, port=None, channel=None, **kwargs):
        super().__init__(**kwargs)
        self.port = port
        self.channel = channel
        self.device.channel_config(port, channel, name=self.name, direction='out')

    async def set_state(self, state):
        await self.device.set_channel_state(self.port, self.channel, state)

    async def setup(self):
        await super().setup()
        await self.device.setup()


@register_hardware()
class MCP23017(Hardware):
    ports = ['a', 'b']
    channels = list(range(8))
    directions = ['in', 'out']

    def __init__(self, address=MCP230XX_DEFAULT_ADDRESS, i2c_bus=0, **kwargs):
        super().__init__(**kwargs)
        self.bus = i2c_manager.get_bus(i2c_bus)
        self.address = address
        self.name = dict()
        self.direction = dict()
        self.pullup = dict()
        self.value = dict()
        self.last_read_time = dict()
        for port in self.ports:
            self.name[port] = dict()
            self.direction[port] = dict()
            self.pullup[port] = dict()
            self.value[port] = dict()
            self.last_read_time[port] = 0
            for channel in self.channels:
                self.direction[port][channel] = '0'
                self.pullup[port][channel] = '0'
                self.value[port][channel] = '0'
        self.channels_reverse = copy(self.channels)
        self.channels_reverse.reverse()
        self.lock = asyncio.Lock()

    def channel_config(self, port, channel, name='', direction='out'):
        if port not in self.ports:
            raise ValidationError('Port should be one of {}'.format(self.ports))
        if channel not in self.channels:
            raise ValidationError('Channel should be one of {}'.format(self.channels))
        if channel in self.name[port]:
            if name:
                msg = "Port '{}' channel {} already used by '{}'".format(port, channel, name)
            else:
                msg = "Port '{}' channel {} already in use".format(port, channel, name)
            raise ValidationError(msg)
        if direction not in self.directions:
            raise ValidationError('Direction should be one of {}'.format(self.directions))
        self.name[port][channel] = name
        self.direction[port][channel] = '0' if direction == 'out' else '1'
        self.pullup[port][channel] = '1' if direction == 'in' else '0'

    async def setup(self):
        await super().setup()
        await self.bus.open()
        for port in self.ports:
            direction = int(''.join([self.direction[port][c] for c in self.channels_reverse]), 2)
            pullup = int(''.join([self.pullup[port][c] for c in self.channels_reverse]), 2)
            async with self.lock:
                await self.bus.write_byte_data(self.address, MCP23017_DIRECTION_REGISTER[port], direction)
                await self.bus.write_byte_data(self.address, MCP23017_PULL_UP_REGISTER[port], pullup)
        for port in self.ports:
            await self.read_port(port)

    async def read_port(self, port):
        async with self.lock:
            value = await self.bus.read_byte_data(self.address, MCP23017_GPIO_REGISTER[port])
        for c in self.channels:
            self.value[port][c] = '1' if value & 1 << c else '0'
        self.last_read_time[port] = time_ns()

    async def write_port(self, port):
        async with self.lock:
            await self.bus.write_byte_data(
                self.address,
                MCP23017_GPIO_REGISTER[port],
                int(''.join([self.value[port][c] for c in self.channels_reverse]), 2),
            )
        await self.read_port(port)

    async def get_channel_state(self, port, channel, delay=200):
        half_delay_ns = delay * 500000
        if time_ns() - self.last_read_time[port] > half_delay_ns:
            await self.read_port(port)
        return 'on' if self.value[port][channel] == '0' else 'off'

    async def set_channel_state(self, port, channel, state):
        self.value[port][channel] = '1' if state == 'on' else '0'
        await self.write_port(port)
