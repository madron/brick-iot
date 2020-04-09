import network
import uasyncio as asyncio
import ubinascii
import utime


class NetworkManager:
    def __init__(self, interface='wifi', config=dict()):
        self.interface_name = interface
        self.config = config.get(interface, dict())
        self.connected = False
        self.interface = None

    async def connect(self):
        if self.interface_name == 'hostspot':
            await self.connect_hotspot(self.config)
        elif self.interface_name == 'wifi':
            await self.connect_wifi(self.config)

    async def connect_hotspot(self, config):
        ssid = config.get('ssid', None)
        password = config.get('password', None)
        if not ssid:
            ssid = 'brick-{}'.format(ubinascii.hexlify(network.WLAN().config('mac'),'').decode())
        print('Starting hotspot "{}" ...'.format(ssid))

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
            print('Interface active')

        # Configure hotspot
        self.interface.config(**kwargs)

        ip = self.interface.ifconfig()[0]
        print('Hotspot "{}" started. Ip: {}'.format(ssid, ip))

    async def connect_wifi(self, config):
        ssid = config['ssid']
        password = config['password']

        print('Connecting to "{}" ...'.format(ssid))
        self.interface = network.WLAN(network.STA_IF)
        self.interface.active(True)
        self.interface.connect(ssid, password)

        # Wait for connection
        while self.interface.status() == network.STAT_CONNECTING:
            await asyncio.sleep_ms(200)
        if not self.interface.isconnected():
            print('Connection failed:', self.interface.status())
            raise OSError

        # Check if connection is stable
        for _ in range(5):
            if not self.interface.isconnected():
                print('Connection failed:', self.interface.status())
                raise OSError
            await asyncio.sleep_ms(200)

        self.ip = self.interface.ifconfig()[0]
        print('Connected to "{}"  Got Ip {}'.format(ssid, self.ip))

    def isconnected(self):
        if self.interface_name == 'hostspot':
            return True
        elif self.interface_name == 'wifi':
            return self.interface.isconnected()
