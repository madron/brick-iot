try:
    from uasyncio import asyncio
except ImportError:
    import asyncio


class Broker:
    def __init__(self, dispatcher, component):
        self.dispatcher = dispatcher
        self.component = component

    def send(self, recipient, topic, payload=None):
        return self.dispatcher.send(self.component, recipient, topic, payload=payload)

    async def subscribe(self, callback, sender=None, topic=None):
        await self.dispatcher.subscribe(self.component, callback, sender=sender, topic=topic)

    async def unsubscribe(self, sender=None, topic=None):
        await self.dispatcher.unsubscribe(self.component, sender=sender, topic=topic)

    def publish(self, topic, payload=None):
        return self.dispatcher.publish(self.component, topic=topic, payload=payload)


class Dispatcher:
    def __init__(self, log):
        self.log = log
        self.callbacks = dict()
        self.subscriptions = dict()

    def get_broker(self, component, callback=None):
        self.callbacks[component] = callback
        return Broker(self, component)

    def send(self, sender, recipient, topic, payload=None):
        if recipient in self.callbacks:
            callback = self.callbacks[recipient]
            if bool(callback):
                log_context = ' - {} -> {}'.format(sender, recipient)
                coro = self._callback_wrapper(log_context, callback, sender=sender, topic=topic, payload=payload)
                return asyncio.create_task(coro)
            else:
                self.log.debug('No callback - {} -> {}'.format(sender, recipient))
        else:
            self.log.debug('No recipient - {} -> {}'.format(sender, recipient))
        return asyncio.sleep(0)

    async def subscribe(self, component, callback, sender, topic):
        components = self.subscriptions.setdefault((sender, topic), dict())
        if component in components:
            self.log.error('Already subscribed - {} -> {} {}'.format(component, sender, topic))
        components[component] = callback

    async def unsubscribe(self, component, sender, topic):
        key = (sender, topic)
        components = self.subscriptions.get(key, dict())
        components.pop(component, None)
        if not components:
            self.subscriptions.pop(key, None)

    def publish(self, sender, topic, payload=None):
        recipients = []
        for key in [(sender, topic), (sender, None), (None, topic), (None, None)]:
            for component, callback in self.subscriptions.get(key, dict()).items():
                recipients.append((component, callback))
        tasks = []
        for component, callback in recipients:
            log_context = ' - c1 <- c event'.format(component, sender, topic)
            tasks.append(asyncio.create_task(self._callback_wrapper(log_context, callback, sender=sender, topic=topic, payload=payload)))
        return asyncio.create_task(self._gather(tasks))

    async def _gather(self, tasks):
        for task in tasks:
            await task

    async def _callback_wrapper(self, log_context, callback, **kwargs):
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
