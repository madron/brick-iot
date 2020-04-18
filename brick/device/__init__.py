import asyncio
import re
from brick.exceptions import ValidationError


def import_device_modules():
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
        self.log.debug('{} {}'.format(topic, payload))
        self._state[topic] = payload
        self.broker.publish(topic=topic, payload=payload)

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
