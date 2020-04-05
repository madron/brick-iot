from brick.config import get_config
from brick.networking import start_networking
from brick.webserver import WebServer


class Application:
    def __init__(self):
        self.config = get_config()
        self.mode = self.config.get('mode', 'normal')

    def run(self):
        # Start networking
        network_config = self.config.get('network', dict())
        start_networking(self.mode, network_config)

        if self.mode == 'config':
            self.config_mode()
        elif self.mode == 'normal':
            self.normal_mode()

    def config_mode(self):
        print('Config mode')
        server = WebServer()
        server.Start()

    def normal_mode(self):
        print('Normal mode')
