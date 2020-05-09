import asyncio
import time
from copy import copy
from brick import validators
from brick.device import Device, register_device
from brick.exceptions import ValidationError
from brick.hardware.gpio import GPIOInput, GPIOOutput
from brick.hardware.mcp.mcp230xx import MCP23017Input, MCP23017Output


DIGITAL_INPUT = dict(
    GPIO=GPIOInput,
    MCP23017=MCP23017Input,
)
DIGITAL_OUTPUT = dict(
    GPIO=GPIOOutput,
    MCP23017=MCP23017Output,
)


class SingleClickHandler:
    def __init__(self, start=None):
        self.start = start or time.time_ns() // 1000000
        self.pressed = False

    def get_events(self, pressed, ms=None):
        if pressed:
            if not self.pressed:
                self.pressed = pressed
                return ['begin', 'single']
        else:
            if self.pressed:
                self.pressed = pressed
                return ['end']
        return []


class LongClickHandler:
    def __init__(self, long_click=1000, start=None):
        self.long_click = long_click
        self.start = start or time.time_ns() // 1000000
        self.pressed = False
        self.is_single_click = False
        self.click_started = None

    def get_events(self, pressed, ms=None):
        if pressed:
            if not self.pressed:
                # Just pressed
                self.pressed = pressed
                self.click_started = ms or time.time_ns() // 1000000
                self.is_single_click = True
                return ['begin']
            else:
                # Still pressed
                if self.click_started:
                    ms = ms or time.time_ns() // 1000000
                    if ms - self.click_started > self.long_click:
                        self.click_started = None
                        self.is_single_click = False
                        return ['long']
        else:
            if self.pressed:
                # Just released
                self.pressed = pressed
                if self.is_single_click:
                    self.is_single_click = False
                    return ['single', 'end']
                return ['end']
        return []


@register_device()
class Button(Device):
    debounce_validator = validators.IntegerValidator(name='debounce', min_value=0)

    def __init__(self, hardware=dict(), debounce=50, long_click=None,
                 on_press=[], on_release=[], on_single_click=[], on_long_click=[], **kwargs):
        super().__init__(**kwargs)
        self.debounce = self.debounce_validator(debounce)
        self.hardware = self.clean_hardware(hardware, delay=self.debounce)
        self.delay = self.debounce / 1000
        self.on_single_click = on_single_click
        self.on_long_click = on_long_click
        self.message_lists = dict(
            begin=self.clean_message_list(on_press),
            end=self.clean_message_list(on_release),
            single=self.clean_message_list(on_single_click),
            long=self.clean_message_list(on_long_click),
        )
        if long_click:
            self.handler = LongClickHandler(long_click=int(long_click))
        else:
            self.handler = SingleClickHandler()

    def clean_hardware(self, hardware, delay):
        hardware = copy(hardware)
        if 'type' not in hardware:
            raise ValidationError('Missing hardware type.')
        hardware_type = hardware.pop('type')
        if hardware_type not in DIGITAL_INPUT:
            msg = "Hardware type '{}' not supported. Choices: {}".format(hardware_type, DIGITAL_INPUT.keys())
            raise ValidationError(msg)
        hardware_class = DIGITAL_INPUT[hardware_type]
        if 'device' in hardware:
            hardware_name = hardware['device']
            device = self.hardware_manager.hardware[hardware_name]
            hardware['device'] = device
        return hardware_class(delay=delay, **hardware)

    def clean_message_list(self, message_list):
        if message_list:
            if not isinstance(message_list[0], list):
                message_list = [message_list]
        return message_list

    async def setup(self):
        await self.hardware.setup()

    async def loop(self):
        # If pressed on start wait until release
        while await self.hardware.is_pressed():
            await asyncio.sleep(self.delay)
        while True:
            for event in self.handler.get_events(await self.hardware.is_pressed()):
                self.event_handler(event)
            await asyncio.sleep(self.delay)

    def event_handler(self, event):
        self.log.debug('click {}'.format(event))
        message_list = self.message_lists[event]
        if message_list:
            for component, topic, payload in message_list:
                self.broker.send(component, topic, payload)
        self.broker.publish(topic='click', payload=event)
        self.broker.publish(topic='click', payload='none')


@register_device()
class Relay(Device):
    debounce_validator = validators.IntegerValidator(name='debounce', min_value=0)
    initial_validator = validators.OnOffValidator(name='initial')

    def __init__(self, hardware=dict(), initial='off', **kwargs):
        super().__init__(**kwargs)
        self.hardware = self.clean_hardware(hardware)
        self.initial = self.initial_validator(initial)

    def clean_hardware(self, hardware):
        hardware = copy(hardware)
        if 'type' not in hardware:
            raise ValidationError('Missing hardware type.')
        hardware_type = hardware.pop('type')
        if hardware_type not in DIGITAL_OUTPUT:
            msg = "Hardware type '{}' not supported. Choices: {}".format(hardware_type, DIGITAL_OUTPUT.keys())
            raise ValidationError(msg)
        hardware_class = DIGITAL_OUTPUT[hardware_type]
        if 'device' in hardware:
            hardware_name = hardware['device']
            device = self.hardware_manager.hardware[hardware_name]
            hardware['device'] = device
        return hardware_class(**hardware)

    async def setup(self):
        await self.hardware.setup()
        await self.set_power(self.initial)

    async def set_power(self, value):
        if value == 'on':
            await self.hardware.set_state(value)
            self.set_state('power', value)
            self.log.debug(value)
        elif value == 'off':
            await self.hardware.set_state(value)
            self.set_state('power', value)
            self.log.debug(value)
        elif value == 'toggle':
            power = self.get_state('power')
            if power == 'on':
                await self.set_power('off')
            if power == 'off':
                await self.set_power('on')

    async def message_received(self, sender=None, topic=None, payload=None):
        if topic == 'power':
            await self.set_power(payload)
