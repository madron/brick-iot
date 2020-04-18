import asyncio
import re
from hbmqtt.client import MQTTClient


class Mqtt:
    def __init__(self, log, broker, name='brick', config=dict()):
        self.log = log
        self.broker = broker
        self.name = name
        self.config = config
        self.prefix = '{}/{}'.format(config.get('prefix', 'brick'), name)
        self.get_prefix = '{}/get'.format(self.prefix)
        self.set_prefix = '{}/set'.format(self.prefix)
        self.last_will_topic = '{}/state'.format(self.get_prefix)
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 1883)
        self.message_re = re.compile('^{}/(.+?)/(.+)$'.format(self.set_prefix))
        self.excluded_components = ['network']
        self.available_components = [x for x in self.broker.dispatcher.callbacks.keys() if not x in self.excluded_components]
        self.client = self.get_client()
        self.connect_parameters = self.get_connect_parameters()

    def get_client(self):
        return MQTTClient(
            client_id=self.config.get('client_id', self.name),
            config=self.get_client_config(),
        )

    def get_client_config(self):
        return dict(
            keep_alive=self.config.get('keep_alive', 5),
            ping_delay=1,
            default_qos=2,
            default_retain=False,
            auto_reconnect=False,
            reconnect_max_interval=5,
            reconnect_retries=-1,
            will=dict(
                retain=True,
                topic=self.last_will_topic,
                message=b'offline',
                qos=1,
            )
        )

    def get_connect_parameters(self):
        auth = ''
        username = self.config.get('username', None)
        password = self.config.get('password', None)
        if username:
            auth = '{}:{}@'.format(username, password)
        return dict(
            uri='mqtt://{}{}:{}/'.format(auth, self.host, self.port),
        )


    async def start(self, **kwargs):
        self.log.info('Started. Server: {}'.format(self.host))
        asyncio.create_task(self.connect())

    async def stop(self, **kwargs):
        self.broker.unsubscribe()
        await self.client.disconnect()
        self.log.info('Stopped')

    async def connect(self):
        await self.client.connect(**self.connect_parameters)
        await self.client.publish(self.last_will_topic, b'online')
        topic = '{}/#'.format(self.set_prefix)
        await self.client.subscribe([(topic, 2)])
        self.log.info('Connected')
        asyncio.create_task(self.read_messages())
        self.broker.subscribe(self.on_event_published)
        asyncio.create_task(self.publish_state())

    async def publish_state(self):
        await asyncio.sleep(1)
        await self.broker.publish(topic='publish_state')

    def _on_message(self, topic, payload, retained):
        asyncio.create_task(self.on_message(topic, payload, retained))

    async def read_messages(self):
        while True:
            try:
                message = await self.client.deliver_message()
                packet = message.publish_packet
                topic = packet.variable_header.topic_name
                payload = packet.payload.data.decode('utf-8')
                await self.on_message(topic, payload)
            except Exception as error:
                self.log.exception('read_messages', error)

    async def on_message(self, topic, payload):
        self.log.debug('message received: {} {}'.format(topic, payload))
        try:
            match = self.message_re.match(topic)
            if match:
                recipient = match.group(1)
                topic = match.group(2)
                if recipient in self.available_components:
                    self.broker.send(recipient, topic, payload)
        except Exception as error:
            self.log.exception('on_message')

    async def on_event_published(self, sender, topic, payload=None):
        if sender in self.available_components:
            self.log.debug('event published: {}/{} {}'.format(sender, topic, payload))
            topic = '{}/{}/{}'.format(self.get_prefix, sender, topic)
            await self.client.publish(topic, str(payload).encode(), True, 1)
