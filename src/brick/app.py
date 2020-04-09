import utime
import uasyncio as asyncio
from brick.config import get_config
from brick.mqtt import MQTTClient
from brick.networking import NetworkManager
from brick.utils import get_iso_timestamp, get_traceback
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
            traceback = get_traceback(error)
            print(traceback)
            with open("error.log", "a") as error_log:
                error_log.write('{} '.format(get_iso_timestamp()))
                error_log.write(traceback)

    async def run(self):
        if self.mode == 'config':
            await self.network.connect()
            self.config_mode()
        elif self.mode == 'normal':
            await self.normal_mode()

    def config_mode(self):
        print('Config mode')
        server = WebServer()
        server.Start()

    def normal_mode(self):
        print('Normal mode')
        self.client = MQTTClient(name=self.name, config=self.mqtt_config, network=self.network)
        await self.mqtt_connect()
        while True:
            await self.client.publish('brick/status', 'online')
            utime.sleep(2)

    async def mqtt_connect(self):
        prefix = self.client.prefix
        availability_topic = '{}/state'.format(prefix)
        await self.client.connect()
        await self.client.publish(topic=availability_topic, msg='online', retain=True, qos=1)
