import asyncio
import decimal
import json
import re
import time
from brick.exceptions import ValidationError


def import_device_modules():
    from brick.device import base
    from brick.device import i2c
    from brick.device import adc
    from brick.device import onewire
    from brick.device import test


_device_registry = dict()


def register_device(device_type=None):
    name = device_type
    def decorator(device_class):
        device_type = name or device_class.__name__
        if device_type in _device_registry:
            raise KeyError('device_type {} is already present.'.format(device_type))
        _device_registry[device_type] = device_class
        return device_class
    return decorator


def validate_device(config):
    re_name = re.compile('^[a-z][a-z0-9_]*$')
    import_device_modules()
    devices = dict()
    errors = dict()
    for device_name, device_config in config.items():
        try:
            device_config = device_config.copy()
            if not re_name.match(device_name):
                raise ValidationError('Name must contains lowercase characters, numbers and _ only.')
            if 'type' not in device_config:
                raise ValidationError('type parameter is required.')
            device_type = device_config.pop('type')
            if device_type not in _device_registry:
                raise ValidationError("type '{}' does not exist.".format(device_type))
            device_class = _device_registry[device_type]
            devices[device_name] = device_class(**device_config)
        except ValidationError as error:
            errors[device_name] = error
        except Exception as error:
            errors[device_name] = ValidationError(str(error))
    if errors:
        raise ValidationError(errors)
    return devices


class DeviceManager:
    def __init__(self, log_collector, dispatcher, config):
        self.log_collector = log_collector
        self.dispatcher = dispatcher
        self.log = self.log_collector.get_logger('devicemanager')
        self.broker = self.dispatcher.get_broker('devicemanager')
        self.config = config
        self.devices = validate_device(config)
        for device_name, instance in self.devices.items():
            instance.log = self.log_collector.get_logger(device_name)
            instance.broker = self.dispatcher.get_broker(device_name,callback=instance._message_received)

    async def start(self):
        for name, device in self.devices.items():
            await device.start()
            await asyncio.sleep(0)

    async def stop(self):
        for device in self.devices.values():
            await device.stop()
            await asyncio.sleep(0)


class Device:
    async def start(self):
        self.log.debug('Started')
        await self._setup()
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        await self._teardown()
        self._task.cancel()
        self.log.debug('Stopped')

    async def _setup(self):
        # Check log and broker
        assert bool(self.log)
        assert bool(self.broker)
        # State
        self._state = dict()
        self._subscriptions = dict()
        # publish_state
        self.subscribe(self.publish_state, None, 'publish_state')
        await self.setup()

    async def _teardown(self):
        await self.teardown()
        for sender, topic in self._subscriptions.keys():
            self.broker.unsubscribe(sender, topic)
        self._subscriptions = dict()

    async def _loop(self):
        while True:
            try:
                await self.loop()
                self.log.warning('loop should run forever')
            except Exception as error:
                self.log.exception('loop error', error)
            await asyncio.sleep(10)

    async def _message_received(self, sender=None, topic=None, payload=None):
        self.log.debug('message_received from {} - {} {}'.format(sender, topic, payload))
        await self.message_received(sender=sender, topic=topic, payload=payload)

    async def publish_state(self, **kwargs):
        self.log.debug('publish_state')
        for topic, payload in self._state.items():
            self.broker.publish(topic=topic, payload=payload)

    def set_state(self, topic, payload):
        self.log.debug('set_state {} {}'.format(topic, payload))
        self._state[topic] = payload
        self.broker.publish(topic=topic, payload=payload)

    def get_state(self, topic):
        return self._state[topic]

    def subscribe(self, callback, sender=None, topic=None):
        self.broker.subscribe(callback, sender=sender, topic=topic)
        self._subscriptions[(sender, topic)] = callback

    async def setup(self):
        pass

    async def teardown(self):
        pass

    async def loop(self):
        while True:
            await asyncio.sleep(10)

    async def message_received(self, sender=None, topic=None, payload=None):
        pass


class Sensor(Device):
    def __init__(self, delay=10, max_delay=0, config_mode=False):
        self.delay = int(delay)
        self.max_delay = int(max_delay)
        self.config_mode = bool(config_mode)
        self.sensor_previous_value = None
        self.sensor_set_state_time = 0

    async def setup(self):
        self.set_state('delay', self.delay)
        self.set_state('max_delay', self.max_delay)
        self.set_state('config_mode', json.dumps(self.config_mode))

    async def loop(self):
        while True:
            await self.set_value()
            await asyncio.sleep(self.delay)

    async def message_received(self, sender=None, topic=None, payload=None):
        if self.config_mode:
            if topic == 'delay':
                self.delay = int(payload)
                self.set_state('delay', self.delay)
            if topic == 'max_delay':
                self.max_delay = int(payload)
                self.set_state('max_delay', self.max_delay)

    async def set_value(self):
        value = await self.get_value()
        value = self.clean_value(value)
        if self.is_changed(value, self.sensor_previous_value):
            self.sensor_set_state_time = time.time_ns()
            self.set_state('value', value)
        else:
            now = time.time_ns()
            if (now - self.sensor_set_state_time) // 1000000000 >= self.max_delay:
                self.sensor_set_state_time = time.time_ns()
                self.set_state('value', value)
        self.sensor_previous_value = value

    async def get_value(self):
        raise NotImplementedError()

    def clean_value(self, value):
        return value

    def is_changed(self, value, previous_value):
        return not(value == previous_value)


class NumericSensor(Sensor):
    def __init__(self, scale=1, precision=0, change_margin=0, unit_of_measurement='', **kwargs):
        super().__init__(**kwargs)
        self.scale = float(scale)
        self.precision = self.clean_precision(precision)
        self.change_margin= decimal.Decimal(change_margin)
        self.unit_of_measurement = unit_of_measurement

    async def setup(self):
        await super().setup()
        self.set_state('scale', self.scale)
        self.set_precision(self.precision)
        self.set_state('change_margin', self.change_margin)
        self.set_state('unit_of_measurement', self.unit_of_measurement)

    def set_precision(self, precision):
        self.precision = self.clean_precision(precision)
        self.set_state('precision', self.precision)
        if self.precision > 0:
            self.precision_quantize = decimal.Decimal('0.{}'.format('0' * self.precision))
        else:
            self.precision_quantize = decimal.Decimal('0')

    def clean_precision(self, precision):
        precision = int(precision)
        assert precision <= 6
        return precision

    def clean_value(self, value):
        value = round(value * self.scale, self.precision)
        return decimal.Decimal(value).quantize(self.precision_quantize)

    def is_changed(self, value, previous_value):
        if previous_value is None:
            return True
        if self.change_margin == 0:
            return not(value == previous_value)
        return bool(abs(value - previous_value) >= self.change_margin)

    async def message_received(self, sender=None, topic=None, payload=None):
        await super().message_received(sender=sender, topic=topic, payload=payload)
        if self.config_mode:
            if topic == 'scale':
                self.scale = float(payload)
                self.set_state('scale', self.scale)
            if topic == 'precision':
                self.set_precision(payload)
            if topic == 'change_margin':
                self.change_margin= decimal.Decimal(payload)
                self.set_state('change_margin', self.change_margin)
