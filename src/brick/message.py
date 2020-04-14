try:
    import uasyncio as asyncio
except ImportError:
    import asyncio


class Broker:
    def __init__(self, dispatcher, component):
        self.dispatcher = dispatcher
        self.component = component

    def send(self, recipient, topic, payload=None):
        return self.dispatcher.send(self.component, recipient, topic, payload=payload)

    def subscribe(self, callback, sender=None, topic=None):
        return self.dispatcher.subscribe(self.component, callback, sender=sender, topic=topic)

    def unsubscribe(self, sender=None, topic=None):
        return self.dispatcher.unsubscribe(self.component, sender=sender, topic=topic)

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
        self.log.debug('send - {} -> {}/{} {}'.format(sender, recipient, topic, payload))
        if recipient in self.callbacks:
            callback = self.callbacks[recipient]
            if bool(callback):
                log_context = ' - {} -> {}'.format(sender, recipient)
                coro = self._callback_wrapper(log_context, callback, sender=sender, topic=topic, payload=payload)
                return asyncio.create_task(coro)
            else:
                self.log.error('No callback - {} -> {}'.format(sender, recipient))
        else:
            self.log.error('No recipient - {} -> {}'.format(sender, recipient))
        return asyncio.sleep(0)

    def subscribe(self, component, callback, sender, topic):
        self.log.debug('subscribe - {} - {}/{}'.format(component, sender, topic))
        components = self.subscriptions.setdefault((sender, topic), dict())
        if component in components:
            self.log.error('Already subscribed - {} -> {}/{}'.format(component, sender, topic))
        components[component] = callback

    def unsubscribe(self, component, sender, topic):
        self.log.debug('unsubscribe - {} - {}/{}'.format(component, sender, topic))
        key = (sender, topic)
        components = self.subscriptions.get(key, dict())
        components.pop(component, None)
        if not components:
            self.subscriptions.pop(key, None)

    def publish(self, sender, topic, payload=None):
        self.log.debug('publish - {}/{} {}'.format(sender, topic, payload))
        recipients = []
        for key in [(sender, topic), (sender, None), (None, topic), (None, None)]:
            for component, callback in self.subscriptions.get(key, dict()).items():
                recipients.append((component, callback))
        tasks = []
        for component, callback in recipients:
            log_context = ' - {} <- {}/{}'.format(component, sender, topic)
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
                self.log.exception('Callback error{}'.format(log_context), error)
        except Exception as error:
            self.log.exception('Callback error{}'.format(log_context), error)
