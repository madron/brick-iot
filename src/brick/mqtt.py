import gc
import uasyncio as asyncio
import mqtt_as


class MQTT_base(mqtt_as.MQTT_base):
    # remove _sta_if
    def __init__(self, config):
        # MQTT config
        self._client_id = config['client_id']
        self._user = config['user']
        self._pswd = config['password']
        self._keepalive = config['keepalive']
        if self._keepalive >= 65536:
            raise ValueError('invalid keepalive time')
        self._response_time = config['response_time'] * 1000  # Repub if no PUBACK received (ms).
        self._max_repubs = config['max_repubs']
        self._clean_init = config['clean_init']  # clean_session state on first connection
        self._clean = config['clean']  # clean_session state on reconnect
        will = config['will']
        if will is None:
            self._lw_topic = False
        else:
            self._set_last_will(*will)
        # WiFi config
        self._ssid = config['ssid']  # Required for ESP32 / Pyboard D. Optional ESP8266
        self._wifi_pw = config['wifi_pw']
        self._ssl = config['ssl']
        self._ssl_params = config['ssl_params']
        # Callbacks and coros
        self._cb = config['subs_cb']
        self._wifi_handler = config['wifi_coro']
        self._connect_handler = config['connect_coro']
        # Network
        self.port = config['port']
        if self.port == 0:
            self.port = 8883 if self._ssl else 1883
        self.server = config['server']
        if self.server is None:
            raise ValueError('no server specified.')
        self._sock = None
        # self._sta_if = network.WLAN(network.STA_IF)
        # self._sta_if.active(True)

        self.newpid = pid_gen()
        self.rcv_pids = set()  # PUBACK and SUBACK pids awaiting ACK response
        self.last_rx = ticks_ms()  # Time of last communication from broker
        self.lock = asyncio.Lock()


async def noop(*args, **kwargs):
    await asyncio.sleep(0)


class MQTTClient(mqtt_as.MQTTClient):
    def __init__(self, config):
        super().__init__(config)
        # Fake methods
        self.wifi_connect = noop
        self._wifi_handler = noop
        self._connect_handler = noop

    # remove _sta_if
    async def _keep_connected(self):
        while self._has_connected:
            if self.isconnected():  # Pause for 1 second
                await asyncio.sleep(1)
                gc.collect()
            else:
                # self._sta_if.disconnect()
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


class Mqtt(MQTTClient):
    def __init__(self, log, broker, name='brick', config=dict()):
        self.log = log
        self.broker = broker
        self.broker.subscribe(self.start, 'network', 'connect')
        self.broker.subscribe(self.stop, 'network', 'disconnect')
        self.prefix = '{}/{}'.format(config.get('prefix', 'brick'), name)
        self.get_prefix = '{}/get'.format(self.prefix)
        self.set_prefix = '{}/set'.format(self.prefix)
        self.last_will_topic = '{}/state'.format(self.get_prefix)
        self.host = config.get('host', 'localhost')
        # Base config
        base_config = mqtt_as.config
        base_config['client_id'] = config.get('client_id', name)
        base_config['server'] = self.host
        base_config['port'] = config.get('port', 1883)
        base_config['user'] = config.get('username', '')
        base_config['password'] = config.get('password', '')
        base_config['keepalive'] = config.get('keepalive', 5)
        base_config['ssl'] = config.get('ssl', False)
        base_config['ssl_params'] = config.get('ssl_params', dict())
        # Last will
        base_config['will'] = [self.last_will_topic, 'offline', True, 1]
        # handler
        base_config['subs_cb'] = self._on_message
        super().__init__(base_config)

    def dprint(self, *args):
        msg = '--- mqtt_as: {}'.format(' '.join(args))
        self.log.debug(msg)

    async def start(self, **kwargs):
        self.log.info('Started. Server: {}'.format(self.host))
        await self.connect()

    async def stop(self, **kwargs):
        await self.disconnect()
        self.log.info('Stopped')

    async def connect(self):
        await super().connect()
        await asyncio.sleep_ms(20)
        await self.publish(self.last_will_topic, 'online', True, 1)
        topic = '{}/#'.format(self.set_prefix)
        await self.subscribe(topic, qos=1)
        self.log.info('Connected')

    def _on_message(self, topic, payload, retained):
        asyncio.create_task(self.on_message(topic, payload, retained))

    async def on_message(self, topic, payload, retained):
        self.log.debug('message received: {} {}'.format(topic, payload))
        topic = topic.decode('utf-8').replace('{}/'.format(self.set_prefix), '', 1)
        payload = payload.decode('utf-8')
        # topic = topic.replace('{}/'.format(self.set_prefix), '', 1)

    # async def write(self, topic, payload):
    #     topic = '{}/{}'.format(self.get_prefix, topic)
    #     await self.client.publish(topic, payload, True, 1)
