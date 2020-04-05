import json
from brick import constants


def get_config(config_dir=''):
    file_name = 'config.json'
    if config_dir:
        file_name = '{}/config.json'.format(config_dir)
    try:
        with open(file_name, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        with open(file_name, 'w') as f:
            f.write(constants.DEFAULT_CONFIG)
        with open(file_name, 'r') as f:
            lines = f.readlines()

    # Skip commented lines
    lines = [l for l in lines if not l.lstrip(' ').startswith('//')]
    config = json.loads(''.join(lines))
    return config
