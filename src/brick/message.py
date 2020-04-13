class Broker:
    def __init__(self, dispatcher, component):
        self.dispatcher = dispatcher
        self.component = component

    async def send(self, recipient, topic, payload=None):
        await self.dispatcher.send(self.component, recipient, topic, payload=payload)

    async def subscribe(self, callback, sender=None, topic=None):
        await self.dispatcher.subscribe(self.component, callback, sender=sender, topic=topic)


class Dispatcher:
    def __init__(self, log):
        self.log = log
        self.brokers = dict()
        self.subscriptions = dict()

    def get_broker(self, component, callback=None):
        self.brokers[component] = dict(callback=callback, subscriptions=dict())
        return Broker(self, component)

    async def send(self, sender, recipient, topic, payload=None):
        if recipient in self.brokers:
            broker = self.brokers[recipient]
            callback = self.brokers[recipient]['callback']
            if bool(callback):
                try:
                    await callback(sender=sender, topic=topic, payload=payload)
                except TypeError as error:
                    description = ''
                    args = getattr(error, 'args', None) or ()
                    if len(args) > 0:
                        description = args[0]
                    if description == "object NoneType can't be used in 'await' expression":
                        self.log.error('Callback not async - {} -> {}'.format(sender, recipient))
                    else:
                        self.log.exception('Callback error - {} -> {}'.format(sender, recipient), error)
                except Exception as error:
                    self.log.exception('Callback error - {} -> {}'.format(sender, recipient), error)
            else:
                self.log.debug('No callback - {} -> {}'.format(sender, recipient))
        else:
            self.log.debug('No recipient - {} -> {}'.format(sender, recipient))

    async def subscribe(self, component, callback, sender, topic):
        key = (sender, topic)
        if key in self.brokers[component]['subscriptions']:
            self.log.error('Already subscribed - {} -> {} {}'.format(component, sender, topic))
        self.brokers[component]['subscriptions'][key] = callback
        components = self.subscriptions.setdefault(key, dict())
        components[component] = callback
