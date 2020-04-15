import uasyncio as asyncio
import usocket as socket
import mqtt_as
from utime import ticks_ms, ticks_diff


_DEFAULT_MS = const(20)


class MQTTClient(mqtt_as.MQTT_base):
    def __init__(self, config):
        self._addr = None
        self._handle_msg_task = None
        self._keep_alive_task = None
        super().__init__(config)
        keepalive = 1000 * self._keepalive  # ms
        self._ping_interval = keepalive // 4 if keepalive else 20000
        p_i = config['ping_interval'] * 1000  # Can specify shorter e.g. for subscribe-only
        if p_i and p_i < self._ping_interval:
            self._ping_interval = p_i

    def isconnected(self):
        return True

    def _reconnect(self):
        pass

    async def connect(self):
        if not self._addr:
            self._addr = socket.getaddrinfo(self.server, self.port)[0][-1]
        await self._connect(True)
        self.rcv_pids.clear()
        self._handle_msg_task = asyncio.create_task(self._handle_msg())
        self._keep_alive_task = asyncio.create_task(self._keep_alive())

    async def disconnect(self):
        await self._handle_msg_task.cancel()
        await self._keep_alive_task.cancel()
        await super().disconnect()

    async def subscribe(self, topic, qos=0):
        mqtt_as.qos_check(qos)
        while True:
            try:
                return await super().subscribe(topic, qos)
            except OSError:
                pass

    async def publish(self, topic, msg, retain=False, qos=0):
        mqtt_as.qos_check(qos)
        while True:
            try:
                return await super().publish(topic, msg, retain, qos)
            except OSError:
                pass

    async def _handle_msg(self):
        while True:
            try:
                async with self.lock:
                    await self.wait_msg()  # Immediate return if no message
                await asyncio.sleep_ms(_DEFAULT_MS)  # Let other tasks get lock
            except OSError as error:
                self.log.exception('_handle_msg', error)


    # Keep broker alive MQTT spec 3.1.2.10 Keep Alive.
    # Runs until ping failure or no response in keepalive period.
    async def _keep_alive(self):
        while True:
            pings_due = ticks_diff(ticks_ms(), self.last_rx) // self._ping_interval
            if pings_due >= 4:
                self.dprint('Reconnect: broker fail.')
                break
            elif pings_due >= 1:
                try:
                    await self._ping()
                except OSError:
                    break
            await asyncio.sleep(1)


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
        base_config['subs_cb'] = self.on_message
        super().__init__(base_config)

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
        print(topic)
        await self.subscribe(topic, qos=1)
        self.log.info('Connected')

    def on_message(self, topic, payload, retained):
        self.log.debug('message received: {} {}'.format(topic, payload))
        topic = topic.decode('utf-8').replace('{}/'.format(self.set_prefix), '', 1)
        payload = payload.decode('utf-8')
        # topic = topic.replace('{}/'.format(self.set_prefix), '', 1)


    # async def write(self, topic, payload):
    #     topic = '{}/{}'.format(self.get_prefix, topic)
    #     await self.client.publish(topic, payload, True, 1)
