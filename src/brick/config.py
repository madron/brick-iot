import json
from brick import constants


def get_config(config_dir=''):
    config_text = get_config_text(config_dir=config_dir)
    return validate_config(config_text)


def get_config_text(config_dir=''):
    file_name = 'config.json'
    if config_dir:
        file_name = '{}/config.json'.format(config_dir)
    try:
        with open(file_name, 'r') as f:
            text = f.read()
    except FileNotFoundError:
        with open(file_name, 'w') as f:
            f.write(constants.DEFAULT_CONFIG)
        with open(file_name, 'r') as f:
            text = f.read()
    return text


def validate_config(config_text):
    lines = config_text.splitlines()
    # Skip commented lines
    lines = [l for l in lines if not l.lstrip(' ').startswith('//')]
    config = json.loads('\n'.join(lines))
    return config


def save_config(config_text, config_dir=''):
    file_name = 'config.json'
    if config_dir:
        file_name = '{}/config.json'.format(config_dir)
    with open(file_name, 'w') as f:
        f.write(config_text)
