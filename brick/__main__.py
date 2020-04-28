import argparse
import os
import time
from brick.app import Application


def main():
    parser = argparse.ArgumentParser(description='Brick')
    parser.add_argument('--config-dir', metavar='D', default=os.getcwd(), dest='config_dir',
                        help='Configuration directory. Default: current directory')
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
