import sys
import time
import asyncio
from brick import web
from brick.config import get_config
from brick.device import DeviceManager
from brick.logging import LogCollector, StdoutLogConsumer
from brick.message import Dispatcher
from brick.mqtt import Mqtt
from brick.networking import NetworkManager
from brick.ntp import NtpSync
from brick.utils import get_traceback


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
        # Dispatcher
        self.dispatcher = Dispatcher(self.log_collector.get_logger('dispatcher'))
        # Device
        self.device = DeviceManager(
            self.log_collector,
            self.dispatcher,
            self.config.get('devices', dict()),
        )
        # Network
        self.network = NetworkManager(
            log=self.log_collector.get_logger('network'),
            broker=self.dispatcher.get_broker('network'),
            config=self.config.get('network', dict()),
        )
        # Ntp
        ntp_config = self.config.get('ntp', dict())
        self.ntp = NtpSync(
            self.log_collector.get_logger('ntp'),
            self.dispatcher.get_broker('ntp'),
            **ntp_config,
        )
        # Mqtt
        self.mqtt = Mqtt(
            self.log_collector.get_logger('mqtt'),
            self.dispatcher.get_broker('mqtt'),
            name=self.name,
            config=self.mqtt_config,
        )
        # Web server
        self.webserver = web.Server(log_collector=self.log_collector)
        self.webserver_task = None

    def start(self):
        self.loop.create_task(self.run())
        self.loop.run_forever()

    async def run(self):
        await self.network.start()
        if self.mode == 'config':
            self.log.info('App started, mode: config')
            await self.config_mode()
        elif self.mode == 'normal':
            self.log.info('App started, mode: normal')
            await self.normal_mode()

    async def config_mode(self):
        self.webserver_task = self.webserver.start()

    async def normal_mode(self):
        await self.device.start()
        if self.config.get('config_mode', '') == 'normal':
            self.webserver_task = self.webserver.start()
