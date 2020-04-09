import gc
import usocket as socket
import uasyncio as asyncio
import mqtt_as
from umqtt.robust import MQTTClient


class MQTTClient(mqtt_as.MQTTClient):
    def __init__(self, name='brick', config=dict(), network=None):
        self.config = config
        self.network = network
        self.prefix = '{}/{}'.format(self.config.get('prefix', 'brick'), name)
        self.last_will_topic = '{}/state'.format(self.prefix)
        base_config = mqtt_as.config
        base_config['client_id'] = config.get('client_id', name)
        base_config['server'] = config.get('host', 'localhost')
        base_config['port'] = config.get('port', 1883)
        base_config['user'] = config.get('username', '')
        base_config['password'] = config.get('password', '')
        base_config['keepalive'] = config.get('keepalive', 5)
        base_config['ssl'] = config.get('ssl', False)
        base_config['ssl_params'] = config.get('ssl_params', dict())
        # Last will
        retain = True
        qos = 1
        base_config['will'] = [self.last_will_topic, 'offline', retain, qos]
        super().__init__(base_config)

    async def connect(self):
        if not self._has_connected:
            await self.network.connect() # On 1st call, caller handles error
            # Note this blocks if DNS lookup occurs. Do it once to prevent
            # blocking during later internet outage:
            self._addr = socket.getaddrinfo(self.server, self.port)[0][-1]
        self._in_connect = True  # Disable low level ._isconnected check
        clean = self._clean if self._has_connected else self._clean_init
        try:
            await self._connect(clean)
        except Exception:
            self.close()
            raise
        self.rcv_pids.clear()
        # If we get here without error broker/LAN must be up.
        self._isconnected = True
        self._in_connect = False  # Low level code can now check connectivity.
        loop = asyncio.get_event_loop()
        loop.create_task(self._wifi_handler(True))  # User handler.
        if not self._has_connected:
            self._has_connected = True  # Use normal clean flag on reconnect.
            loop.create_task(
                self._keep_connected())  # Runs forever unless user issues .disconnect()

        loop.create_task(self._handle_msg())  # Tasks quit on connection fail.
        loop.create_task(self._keep_alive())
        if self.DEBUG:
            loop.create_task(self._memory())
        loop.create_task(self._connect_handler(self))  # User handler.

    def isconnected(self):
        if self._in_connect:  # Disable low-level check during .connect()
            return True
        if self._isconnected and not self.network.isconnected():  # It's going down.
            self._reconnect()
        return self._isconnected

    # Scheduled on 1st successful connection. Runs forever maintaining wifi and
    # broker connection. Must handle conditions at edge of WiFi range.
    async def _keep_connected(self):
        while self._has_connected:
            if self.isconnected():  # Pause for 1 second
                await asyncio.sleep(1)
                gc.collect()
            else:
                self._sta_if.disconnect()
                await asyncio.sleep(1)
                try:
                    await self.wifi_connect()
                except OSError:
                    continue
                if not self._has_connected:  # User has issued the terminal .disconnect()
                    self.dprint('Disconnected, exiting _keep_connected')
                    break
                try:
                    await self.connect()
                    # Now has set ._isconnected and scheduled _connect_handler().
                    self.dprint('Reconnect OK!')
                except OSError as e:
                    self.dprint('Error in reconnect.', e)
                    # Can get ECONNABORTED or -1. The latter signifies no or bad CONNACK received.
                    self.close()  # Disconnect and try again.
                    self._in_connect = False
                    self._isconnected = False
        self.dprint('Disconnected, exited _keep_connected')
