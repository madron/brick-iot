import asyncio
import gpiozero
from brick.device import Device, register_device


@register_device()
class Button(Device):
    def __init__(self, pin=None, debounce=50, on_single_click=[]):
        self.pin = int(pin)
        self.debounce = int(debounce)
        self.delay = self.debounce / 1000
        self.on_single_click = on_single_click
        if self.on_single_click:
            if not isinstance(self.on_single_click[0], list):
                self.on_single_click = [self.on_single_click]

    async def setup(self):
        self.button = gpiozero.Button(self.pin)

    async def loop(self):
        pressed = self.button.is_pressed
        while True:
            if self.button.is_pressed:
                if not pressed:
                    self.single_click()
            pressed = self.button.is_pressed
            await asyncio.sleep(self.delay)

    def single_click(self):
        self.log.debug('single_click')
        if self.on_single_click:
            for component, topic, payload in self.on_single_click:
                self.broker.send(component, topic, payload)
        self.broker.publish(topic='click', payload='single')
        self.broker.publish(topic='click', payload='none')


@register_device()
class Relay(Device):
    def __init__(self, pin=None, initial='off'):
        self.pin = int(pin)
        self.initial = 'off'
        if initial in ('on', True):
            self.initial = 'on'

    async def setup(self):
        self.relay = gpiozero.LED(self.pin)
        self.set_power(self.initial)

    def set_power(self, value):
        if value == 'on':
            self.relay.on()
            self.set_state('power', 'on')
            self.log.debug('on')
        if value == 'off':
            self.relay.off()
            self.set_state('power', 'off')
            self.log.debug('off')
        if value == 'toggle':
            power = self.get_state('power')
            if power == 'on':
                self.set_power('off')
            if power == 'off':
                self.set_power('on')

    async def message_received(self, sender=None, topic=None, payload=None):
        if topic == 'power':
            self.set_power(payload)
