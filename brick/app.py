import sys
import time
import asyncio
from brick import web
from brick.component import FakeComponent
from brick.config import ConfigManager
from brick.device import DeviceManager
from brick.hardware import HardwareManager
from brick.logging import LogCollector, StdoutLogConsumer
from brick.message import Dispatcher
from brick.mqtt import Mqtt
from brick.ntp import NtpSync


class Application:
    def __init__(self, config_dir=None, persist_command=None):
        # Config
        self.config_manager = ConfigManager(config_dir=config_dir, persist_command=persist_command)
        self.config = self.config_manager.get_sync()
        self.name = self.config.get('name', 'brick')
        self.mode = self.config.get('mode', 'normal')
        self.mqtt_config = self.config.get('mqtt', dict())
        # Logging
        log_config = self.config.get('log', dict())
        self.log_collector = LogCollector()
        self.stdout_logger = StdoutLogConsumer(
            self.log_collector,
            level=log_config.get('default', 'info'),
            components=log_config.get('components', dict()),
        )
        self.log = self.log_collector.get_logger('app')
        # ConfigManager log
        self.config_manager.set_log(self.log_collector.get_logger('config'))
        # Dispatcher
        self.dispatcher = Dispatcher(self.log_collector.get_logger('dispatcher'))
        # Hardware
        try:
            self.hardware = HardwareManager(
                self.log_collector,
                self.dispatcher,
                self.config.get('hardware', dict()),
            )
        except Exception as error:
            self.hardware = FakeComponent()
            self.log.exception('hardware component discarded', error)
        # Device
        try:
            self.device = DeviceManager(
                self.log_collector,
                self.dispatcher,
                self.hardware,
                self.config.get('devices', dict()),
            )
        except Exception as error:
            self.device = FakeComponent()
            self.log.exception('device component discarded', error)
        # Ntp
        try:
            self.ntp = NtpSync(
                self.log_collector.get_logger('ntp'),
                self.dispatcher.get_broker('ntp'),
                self.config.get('ntp', dict()),
            )
        except Exception as error:
            self.ntp = FakeComponent()
            self.log.exception('ntp component discarded', error)
        # Mqtt
        try:
            self.mqtt = Mqtt(
                self.log_collector.get_logger('mqtt'),
                self.dispatcher.get_broker('mqtt'),
                name=self.name,
                config=self.mqtt_config,
            )
        except Exception as error:
            self.mqtt = FakeComponent()
            self.log.exception('mqtt component discarded', error)
        # Web server
        try:
            self.web = web.Server(
                log_collector=self.log_collector,
                broker=self.dispatcher.get_broker('web'),
                config_manager=self.config_manager,
                config=self.config.get('web', dict()),
            )
        except Exception as error:
            self.web = FakeComponent()
            self.log.exception('web component discarded')

    def start(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.run())
        loop.run_forever()

    async def run(self):
        await self.device.start()
        # await self.ntp.start()
        await self.mqtt.start()
        await self.web.start()
