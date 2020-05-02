import argparse
import os
import time
from brick.app import Application

DEFAULT_CONFIG_DIR = os.path.join(os.getcwd(), 'config')


def main():
    parser = argparse.ArgumentParser(description='Brick')
    parser.add_argument('--config-dir', metavar='D', default=DEFAULT_CONFIG_DIR, dest='config_dir',
                        help='Configuration directory. Default: config directory')
    parser.add_argument('--persist-command', metavar='C', dest='persist_command',
                        help='Command to make config persistent. Example: "/sbin/lbu commit -d"')
    kwargs = vars(parser.parse_args())
    app = Application(**kwargs)
    while True:
        app.start()
        # Wait a little before restarting app
        time.sleep(5)
        print('Restarting app')


if __name__ == '__main__':
    main()
