import network
import uasyncio as asyncio
import ubinascii
import utime


class NetworkManager:
    def __init__(self, log, broker, interface='wifi', config=dict(),
                 on_start=None, on_stop=None, on_connect=None, on_disconnect=None):
        self.log = log
        self.broker = broker
        self.interface_name = interface
        self.config = config.get(interface, dict())
        self.check_delay = self.config.get('check_delay', 1)
        self.fail_delay = self.config.get('fail_delay', 30)
        # State
        self.interface = None
        self.connecting = False
        self.first_connection = True
        self.task = None
        self.ip = None

    async def callback_wrapper(self, callback, **kwargs):
        try:
            await callback
        except Exception as error:
            self.log.exception('Error in callback', error)

    async def on_start(self, **kwargs):
        message = 'Started'
        if kwargs:
            message = '{} {}'.format(message, kwargs)
        self.log.info(message)
        await self.broker.publish('start')

    async def on_stop(self, **kwargs):
        message = 'Stopped'
        if kwargs:
            message = '{} {}'.format(message, kwargs)
        self.log.info(message)
        await self.broker.publish('stop')

    async def on_connect(self, **kwargs):
        message = 'Connected'
        if kwargs:
            message = '{} {}'.format(message, kwargs)
        self.log.info(message)
        await self.broker.publish('connect', payload=kwargs)

    async def on_disconnect(self, **kwargs):
        message = 'Disconnected'
        if kwargs:
            message = '{} {}'.format(message, kwargs)
        self.log.info(message)
        await self.broker.publish('disconnect', payload=kwargs)

    async def start(self, delay=0):
        await asyncio.sleep(delay)
        if self.task:
            self.log.warning('Already started.')
            return
        await self.on_start()
        self.first_connection = True
        self.task = asyncio.create_task(self.check_connection())
        await asyncio.sleep(0)

    async def start_later(self, delay):
        self.log.info('Starting in {} seconds'.format(delay))
        asyncio.create_task(self.start(delay))
        await asyncio.sleep(0)

    async def stop(self, delay=0):
        await asyncio.sleep(delay)
        await self.on_stop()
        self.task.cancel()
        await asyncio.sleep(0)
        self.interface.disconnect()
        self.task = None
        await self.on_disconnect(reason='stop')

    async def stop_later(self, delay):
        self.log.info('Stopping in {} seconds'.format(delay))
        asyncio.create_task(self.stop(delay))
        await asyncio.sleep(0)

    async def check_connection(self):
        while True:
            if not self.isconnected():
                if not self.first_connection:
                    self.log.warning('Connection drop')
                    await self.on_disconnect(reason='failure')
                await self.connect()
            await asyncio.sleep(self.check_delay)

    async def connect(self):
        if self.connecting:
            self.log.warning('Already connecting.')
            return
        self.connecting = True
        while not self.isconnected():
            try:
                if self.interface_name == 'hostspot':
                    await self.connect_hotspot(self.config)
                elif self.interface_name == 'wifi':
                    await self.connect_wifi(self.config)
            except Exception as error:
                self.log.exception('Connection error', error)
                await asyncio.sleep(self.fail_delay)
        self.first_connection = False
        self.connecting = False
        await self.on_connect(ip=self.ip)

    async def connect_hotspot(self, config):
        ssid = config.get('ssid', None)
        password = config.get('password', None)
        if not ssid:
            ssid = 'brick-{}'.format(ubinascii.hexlify(network.WLAN().config('mac'),'').decode())
        self.log.info('Starting hotspot "{}" ...'.format(ssid))

        self.interface = network.WLAN(network.AP_IF)
        kwargs = dict(essid=ssid, dhcp_hostname='brick')
        if password:
            kwargs['authmode'] = network.AUTH_WPA2_PSK
            kwargs['password'] = password
        self.interface.active(True)

        # Check interface
        while not self.interface.active():
            asyncio.sleep_ms(200)
        asyncio.sleep_ms(200)
        if self.interface.active():
            self.log.info('Interface active')

        # Configure hotspot
        self.interface.config(**kwargs)

        ip = self.interface.ifconfig()[0]
        self.log.info('Hotspot "{}" started. Ip: {}'.format(ssid, ip))

    async def connect_wifi(self, config):
        ssid = config['ssid']
        password = config['password']

        self.log.info('Connecting to "{}" ...'.format(ssid))
        self.interface = network.WLAN(network.STA_IF)
        self.interface.active(True)
        self.interface.connect(ssid, password)

        # Wait for connection
        counter = 0
        while self.interface.status() == network.STAT_CONNECTING:
            counter += 1
            if counter > 20:
                counter = 0
                self.log.info('Waiting for connection')
            await asyncio.sleep_ms(500)
        if not self.interface.isconnected():
            self.log.error('Connection failed:', self.interface.status())
            raise OSError

        # Check if connection is stable
        for _ in range(5):
            if not self.interface.isconnected():
                self.log.error('Connection failed:', self.interface.status())
                raise OSError
            await asyncio.sleep_ms(500)

        self.ip = self.interface.ifconfig()[0]
        self.log.debug('Got Ip {}'.format(self.ip))

    def isconnected(self):
        if self.interface_name == 'hostspot':
            return True
        elif self.interface_name == 'wifi':
            if not self.interface:
                return False
            return self.interface.isconnected()
