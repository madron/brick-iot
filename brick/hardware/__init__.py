import asyncio
import json
import re
import time
from decimal import Decimal
from brick import validators
from brick.exceptions import ValidationError


def import_hardware_modules():
    from brick.hardware.mcp import mcp230xx


_hardware_registry = dict()


def register_hardware(hardware_type=None):
    name = hardware_type
    def decorator(hardware_class):
        hardware_type = name or hardware_class.__name__
        if hardware_type in _hardware_registry:
            raise KeyError('hardware_type {} is already present.'.format(hardware_type))
        _hardware_registry[hardware_type] = hardware_class
        return hardware_class
    return decorator


def validate_hardware(config):
    re_name = re.compile('^[a-z][a-z0-9_]*$')
    import_hardware_modules()
    hardware_devices = dict()
    errors = dict()
    for hardware_name, hardware_config in config.items():
        try:
            hardware_config = hardware_config.copy()
            if not re_name.match(hardware_name):
                raise ValidationError('Name must contains lowercase characters, numbers and _ only.')
            if 'type' not in hardware_config:
                raise ValidationError('type parameter is required.')
            hardware_type = hardware_config.pop('type')
            if hardware_type not in _hardware_registry:
                raise ValidationError("type '{}' does not exist.".format(hardware_type))
            hardware_class = _hardware_registry[hardware_type]
            hardware_devices[hardware_name] = hardware_class(**hardware_config)
        except ValidationError as error:
            errors[hardware_name] = error
        except Exception as error:
            errors[hardware_name] = ValidationError(str(error))
    if errors:
        raise ValidationError(errors)
    return hardware_devices


class HardwareManager:
    def __init__(self, log_collector, dispatcher, config):
        self.log_collector = log_collector
        self.dispatcher = dispatcher
        self.log = self.log_collector.get_logger('hardwaremanager')
        self.broker = self.dispatcher.get_broker('hardwaremanager')
        self.config = config
        self.hardware = validate_hardware(config)
        for hardware_name, instance in self.hardware.items():
            instance.log = self.log_collector.get_logger(hardware_name)

    async def start(self):
        for name, hardware in self.hardware.items():
            await hardware.setup()
            await asyncio.sleep(0)

    async def stop(self):
        pass


class Hardware:
    async def setup(self):
        pass
