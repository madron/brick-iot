try:
    from uasyncio import asyncio
except ImportError:
    import asyncio


class Broker:
    def __init__(self, dispatcher, component):
        self.dispatcher = dispatcher
        self.component = component

    async def send(self, recipient, topic, payload=None):
        await self.dispatcher.send(self.component, recipient, topic, payload=payload)

    async def subscribe(self, callback, sender=None, topic=None):
        await self.dispatcher.subscribe(self.component, callback, sender=sender, topic=topic)

    async def publish(self, topic, payload=None):
        await self.dispatcher.publish(self.component, topic=topic, payload=payload)


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
                log_context = ' - {} -> {}'.format(sender, recipient)
                await self.callback_wrapper(log_context, callback, sender=sender, topic=topic, payload=payload)
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

    async def publish(self, sender, topic, payload=None):
        recipients = []
        for key in [(sender, topic), (sender, None), (None, topic), (None, None)]:
            for component, callback in self.subscriptions.get(key, dict()).items():
                recipients.append((component, callback))
        tasks = []
        for component, callback in recipients:
            tasks.append((component, asyncio.create_task(callback(sender=sender, topic=topic, payload=payload))))
        for component, task in tasks:
            log_context = ' - c1 <- c event'.format(component, sender, topic)
            await self.callback_wrapper(log_context, task)

    async def publish(self, sender, topic, payload=None):
        recipients = []
        for key in [(sender, topic), (sender, None), (None, topic), (None, None)]:
            for component, callback in self.subscriptions.get(key, dict()).items():
                recipients.append((component, callback))
                await asyncio.sleep(0)
            await asyncio.sleep(0)
        tasks = []
        for component, callback in recipients:
            log_context = ' - c1 <- c event'.format(component, sender, topic)
            tasks.append((component, asyncio.create_task(self.callback_wrapper(log_context, callback, sender=sender, topic=topic, payload=payload))))
            await asyncio.sleep(0)
        for component, task in tasks:
            await task

    async def callback_wrapper(self, log_context, callback, **kwargs):
        try:
            await callback(**kwargs)
        except TypeError as error:
            description = ''
            args = getattr(error, 'args', None) or ()
            if len(args) > 0:
                description = args[0]
            if description == "object NoneType can't be used in 'await' expression":
                self.log.error('Callback not async{}'.format(log_context))
            else:
                self.log.exception('Callback error{}'.format(log_context))
        except Exception as error:
            self.log.exception('Callback error{}'.format(log_context))
