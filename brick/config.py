import os
import subprocess
import sys
import yaml
from brick import constants
from brick.device import validate_device
from brick.exceptions import ValidationError
from brick.hardware import HardwareManager, validate_hardware
from brick.logging import LogCollector
from brick.message import Dispatcher


class ConfigManager:
    def __init__(self, config_dir=None, persist_command=None):
        self.config_dir = config_dir or ''
        self.persist_command_args = None
        if persist_command:
            self.persist_command_args = persist_command.split(' ')
        self.config_file_name = os.path.join(self.config_dir, 'config.yml')
        self.log = None

    def set_log(self, log):
        self. log = log

    def get(self):
        try:
            with open(self.config_file_name, 'r') as f:
                text = f.read()
        except FileNotFoundError:
            text = constants.DEFAULT_CONFIG
            self.save(text)
        return self.validate(text)

    def validate(self, config_text):
        config = yaml.safe_load(config_text)
        # Hardware
        hardware_config = config.get('hardware', dict())
        validate_hardware(hardware_config)
        # Device
        log_collector = LogCollector()
        dispatcher = Dispatcher(log_collector.get_logger('config'))
        hardware_manager = HardwareManager(log_collector, dispatcher, hardware_config)
        validate_device(config.get('devices', dict()), hardware_manager)
        return config

    def save(self, config_text):
        with open(self.config_file_name, 'w') as f:
            f.write(config_text)
        if self.persist_command_args:
            try:
                subprocess.run(self.persist_command_args, check=True)
            except Exception as error:
                if self.log:
                    self.log.exception('Failed to save config.', error)
                else:
                    raise
