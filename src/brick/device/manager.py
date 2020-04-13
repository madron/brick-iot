import uasyncio as asyncio
from brick.device import test


DEVICE_CLASS = {
    'test-random': test.Random,
    'test-state-publish': test.StatePublish,
}


def get_device_instance(name, config):
        device_class = DEVICE_CLASS[config.pop('type')]
        return device_class(**config)


class DeviceManager:
    def __init__(self, log_collector, dispatcher, config):
        self.log_collector = log_collector
        self.dispatcher = dispatcher
        self.log = self.log_collector.get_logger('devicemanager')
        self.broker = self.dispatcher.get_broker('devicemanager')
        self.config = config
        self.devices = dict()
        for device_name, device_config in config.items():
            try:
                instance = get_device_instance(device_name, device_config)
                instance.log = self.log_collector.get_logger(device_name)
                instance.broker = self.dispatcher.get_broker(device_name,callback=instance.message_callback)
                self.devices[device_name] = instance
            except Exception as error:
                self.log.exception('Device {} discarded'.format(device_name), error)

    async def start(self):
        for name, device in self.devices.items():
            await device.start()
            await asyncio.sleep(0)

    async def stop(self):
        for device in self.devices.values():
            await device.stop()
            await asyncio.sleep(0)
