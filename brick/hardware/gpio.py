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

    async def get_state(self):
        return self.get_contact_value('on' if self.output.is_lit else 'off')

    async def set_state(self, value):
        value = self.get_contact_value(value)
        if value == 'on':
            self.output.on()
        if value == 'off':
            self.output.off()
