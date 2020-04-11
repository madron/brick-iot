import gc
import usocket as socket
import uasyncio as asyncio
import mqtt_as


class MQTTClient(mqtt_as.MQTTClient):
    def __init__(self, name='brick', config=dict(), network=None,
                 last_will_topic='', connect_handler=None, message_handler=None):
        # self.config = config
        self.network = network
        self.last_will_topic = last_will_topic
        self.connect_handler = connect_handler
        self.message_handler = message_handler
        self.loop = asyncio.get_event_loop()
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
        base_config['will'] = [last_will_topic, 'offline', True, 1]
        # handler
        base_config['connect_coro'] = self.on_connect
        base_config['subs_cb'] = self.on_message
        super().__init__(base_config)

    async def on_connect(self, client):
        await client.publish(self.last_will_topic, 'online', True, 1)
        if self.connect_handler:
            await self.connect_handler(client)

    def on_message(self, topic, payload, retained):
        if self.message_handler:
            self.loop.create_task(self.message_handler(topic.decode('utf-8'), payload.decode('utf-8'), retained))

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


class MQTTManager:
    def __init__(self, name='brick', config=dict(), network=None,
                 connect_callback=None, message_callback=None):
        self.prefix = '{}/{}'.format(config.get('prefix', 'brick'), name)
        self.get_prefix = '{}/get'.format(self.prefix)
        self.set_prefix = '{}/set'.format(self.prefix)
        last_will_topic = '{}/state'.format(self.get_prefix)
        self.connect_callback = connect_callback
        self.message_callback = message_callback
        self.client = MQTTClient(
            name=name,
            config=config,
            network=network,
            last_will_topic=last_will_topic,
            connect_handler=self.on_connect,
            message_handler=self.on_message,
        )

    async def start(self):
        await self.client.connect()

    async def on_connect(self, client):
        topic = '{}/#'.format(self.set_prefix)
        await client.subscribe(topic, 1)
        if self.connect_callback:
            await self.connect_callback()

    async def on_message(self, topic, payload, retained):
        if self.message_callback:
            topic = topic.replace('{}/'.format(self.set_prefix), '', 1)
            await self.message_callback(topic, payload)

    async def write(self, topic, payload):
        topic = '{}/{}'.format(self.get_prefix, topic)
        await self.client.publish(topic, payload, True, 1)
