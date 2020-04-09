import sys
import utime
import uasyncio as asyncio
from brick.config import get_config
from brick.mqtt import get_mqtt_client
from brick.networking import NetworkManager
from brick.webserver import WebServer


class Application:
    def __init__(self):
        self.config = get_config()
        self.name = self.config.get('name', 'brick')
        self.mode = self.config.get('mode', 'normal')
        self.mqtt_config = self.config.get('mqtt', dict())
        self.network = self.get_network_manager()
        self.loop = asyncio.get_event_loop()

    def get_network_manager(self):
        if self.mode == 'config':
            interface = self.config.get('config_interface', 'hostspot')
        else:
            interface = self.config.get('interface', 'wifi')
        return NetworkManager(interface=interface, config=self.config.get('network', dict()))

    def start(self):
        try:
            self.loop.create_task(self.run())
            self.loop.run_forever()
        except Exception as error:
            sys.print_exception(error)
            with open("error.log", "a") as error_log:
                timestamp = '{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d} '.format(*utime.localtime())
                error_log.write(timestamp)
                sys.print_exception(error, error_log)

    async def run(self):
        # Start networking
        await self.network.connect()
        #
        if self.mode == 'config':
            self.config_mode()
        elif self.mode == 'normal':
            await self.normal_mode()

    def config_mode(self):
        print('Config mode')
        server = WebServer()
        server.Start()

    def normal_mode(self):
        # count = 0
        # while True:
        #     count += 1
        #     print(count)
        #     await asyncio.sleep(1)
        # #
        print('Normal mode')
        self.client = get_mqtt_client(name=self.name, config=self.mqtt_config)
        self.mqtt_connect()
        while True:
            self.client.publish('brick/status', 'online')
            utime.sleep(2)

    def mqtt_connect(self):
        prefix = '{}/{}'.format(self.mqtt_config.get('prefix', 'brick'), self.name)
        availability_topic = '{}/state'.format(prefix)
        self.client.set_last_will(topic=availability_topic, msg='offline', retain=True, qos=1)
        self.client.connect()
        self.client.publish(topic=availability_topic, msg='online', retain=True, qos=1)
