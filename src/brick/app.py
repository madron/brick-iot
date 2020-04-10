import utime
import uasyncio as asyncio
from brick import web
from brick.config import get_config
from brick.mqtt import MQTTManager
from brick.networking import NetworkManager
from brick.utils import get_iso_timestamp, get_traceback


class Application:
    def __init__(self):
        self.config = get_config()
        self.name = self.config.get('name', 'brick')
        self.mode = self.config.get('mode', 'normal')
        self.mqtt_config = self.config.get('mqtt', dict())
        self.network = self.get_network_manager()
        self.loop = asyncio.get_event_loop()
        self.webserver = web.Server()
        self.webserver_task = None

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
        self.webserver_task = self.webserver.start()

    def normal_mode(self):
        print('Normal mode')
        self.mqtt = MQTTManager(name=self.name, config=self.mqtt_config, network=self.network,
                                connect_callback=self.on_connect, message_callback=self.on_message)
        await self.mqtt.start()
        if self.config.get('config_mode', '') == 'normal':
            self.webserver_task = self.webserver.start()

    async def write_timestamp(self):
        while True:
            await self.mqtt.write('timestamp', get_iso_timestamp())
            await asyncio.sleep(5)

    async def on_connect(self):
        self.loop.create_task(self.write_timestamp())

    async def on_message(self, topic, payload):
        if topic == 'color':
            await self.mqtt.write('color', payload)
