import gpiozero
from brick import validators
from brick.hardware.base import DigitalInput, DigitalOutput


pin_validator = validators.IntegerValidator('pin', min_value=0)


class GPIOInput(DigitalInput):
    def __init__(self, pin=None, **kwargs):
        super().__init__(**kwargs)
        self.pin = pin_validator(pin)

    async def setup(self):
        self.input = gpiozero.Button(self.pin)

    async def is_pressed(self):
        return self.input.is_pressed

    async def get_state(self):
        return 'on' if self.input.is_pressed else 'off'


class GPIOOutput(DigitalOutput):
    def __init__(self, pin=None, **kwargs):
        super().__init__(**kwargs)
        self.pin = pin_validator(pin)

    async def setup(self):
        self.output = gpiozero.LED(self.pin)

    async def set_state(self, state):
        if state == 'on':
            self.output.on()
        if state == 'off':
            self.output.off()

    async def on(self):
        self.output.on()

    async def off(self):
        self.output.off()
