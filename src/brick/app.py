import utime
import uasyncio as asyncio
from brick import web
from brick.config import get_config
from brick.logging import LogCollector, StdoutLogConsumer
from brick.mqtt import MQTTManager
from brick.networking import NetworkManager
from brick.ntp import NtpSync
from brick.utils import get_iso_timestamp, get_traceback


class Application:
    def __init__(self):
        # Config
        self.config = get_config()
        self.name = self.config.get('name', 'brick')
        self.mode = self.config.get('mode', 'normal')
        self.mqtt_config = self.config.get('mqtt', dict())
        # Asyncio loop
        self.loop = asyncio.get_event_loop()
        # Logging
        log_config = self.config.get('log', dict())
        self.log_collector = LogCollector()
        self.stdout_logger = StdoutLogConsumer(
            self.log_collector,
            level=log_config.get('default', 'info'),
            components=log_config.get('components', dict()),
        )
        self.log = self.log_collector.get_logger('app')
        # Network
        self.network = self.get_network_manager()
        # Ntp
        ntp_config = self.network.config.get('ntp', dict())
        self.ntp = NtpSync(self.log_collector.get_logger('ntp'), **ntp_config)
        # Web server
        self.webserver = web.Server(log=self.log_collector.get_logger('web'))
        self.webserver_task = None

    def get_network_manager(self):
        if self.mode == 'config':
            interface = self.config.get('config_interface', 'hostspot')
        else:
            interface = self.config.get('interface', 'wifi')
        return NetworkManager(
            log=self.log_collector.get_logger('network'),
            interface=interface,
            config=self.config.get('network', dict()),
        )

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
            self.log.info('App started, mode: config')
            await self.network.connect()
            self.config_mode()
        elif self.mode == 'normal':
            self.log.info('App started, mode: normal')
            await self.normal_mode()

    def config_mode(self):
        self.webserver_task = self.webserver.start()

    def normal_mode(self):
        self.mqtt = MQTTManager(name=self.name, config=self.mqtt_config, network=self.network,
                                connect_callback=self.on_connect, message_callback=self.on_message)
        await self.mqtt.start()
        await self.ntp.start()
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
