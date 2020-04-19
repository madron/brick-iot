import os
import yaml
from brick import constants
from brick.device import validate_device
from brick.exceptions import ValidationError


def get_config(config_dir=''):
    file_name = os.path.join(config_dir, 'config.yml')
    try:
        with open(file_name, 'r') as f:
            text = f.read()
    except FileNotFoundError:
        with open(file_name, 'w') as f:
            f.write(constants.DEFAULT_CONFIG)
        with open(file_name, 'r') as f:
            text = f.read()

    return validate_config(text)


def validate_config(config_text):
    config = yaml.load(config_text)
    validate_device(config.get('devices', dict()))
    return config


def save_config(config_text, config_dir=''):
    file_name = 'config.json'
    if config_dir:
        file_name = '{}/config.json'.format(config_dir)
    with open(file_name, 'w') as f:
        f.write(config_text)
