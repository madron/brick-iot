import asyncio
import re

class Mqtt:
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
        self.message_re = re.compile('^{}/(.+?)/(.+)$'.format(self.set_prefix))
        self.excluded_components = ['network']
        self.available_components = [x for x in self.broker.dispatcher.callbacks.keys() if not x in self.excluded_components]

    async def start(self, **kwargs):
        self.log.info('TO BE IMPLEMENTED Started. Server: {}'.format(self.host))
        # await self.connect()
        self.broker.subscribe(self.on_event_published)
        asyncio.create_task(self.publish_state())

    async def stop(self, **kwargs):
        self.broker.unsubscribe()
        # await self.disconnect()
        self.log.info('Stopped')

    async def connect(self):
        await super().connect()
        await asyncio.sleep_ms(20)
        await self.publish(self.last_will_topic, 'online', True, 1)
        topic = '{}/#'.format(self.set_prefix)
        await self.subscribe(topic, qos=1)
        self.log.info('Connected')

    async def publish_state(self):
        await asyncio.sleep(1)
        await self.broker.publish(topic='publish_state')

    def _on_message(self, topic, payload, retained):
        asyncio.create_task(self.on_message(topic, payload, retained))

    async def on_message(self, topic, payload, retained):
        self.log.debug('message received: {} {}'.format(topic, payload))
        try:
            topic = topic.decode('utf-8')
            match = self.message_re.match(topic)
            if match:
                recipient = match.group(1)
                topic = match.group(2)
                if recipient in self.available_components:
                    self.broker.send(recipient, topic, payload.decode('utf-8'))
        except Exception as error:
            self.log.debug('on_message', error)

    async def on_event_published(self, sender, topic, payload=None):
        if sender in self.available_components:
            self.log.debug('event published: {}/{} {}'.format(sender, topic, payload))
            topic = '{}/{}/{}'.format(self.get_prefix, sender, topic)
            await self.publish(topic, str(payload), True, 1)
