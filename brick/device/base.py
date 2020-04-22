import asyncio
import time
import gpiozero
from brick.device import Device, register_device


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
    def __init__(self, pin=None, debounce=50, long_click=None,
                 on_press=[], on_release=[], on_single_click=[], on_long_click=[]):
        self.pin = int(pin)
        self.debounce = int(debounce)
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

    def clean_message_list(self, message_list):
        if message_list:
            if not isinstance(message_list[0], list):
                message_list = [message_list]
        return message_list

    async def setup(self):
        self.button = gpiozero.Button(self.pin)

    async def loop(self):
        # If pressed on start wait until release
        while self.button.is_pressed:
            await asyncio.sleep(self.delay)
        while True:
            for event in self.handler.get_events(self.button.is_pressed):
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
