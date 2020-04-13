import unittest
from .test import Callback, Logger
from brick.message import Broker, Dispatcher


class DispatcherTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.log = Logger()
        self.dispatcher = Dispatcher(log=self.log)

    def test_init(self):
        self.assertEqual(self.dispatcher.brokers, dict())

    def test_get_broker_no_callback(self):
        broker = self.dispatcher.get_broker('test')
        self.assertIsInstance(broker, Broker)
        self.assertEqual(broker.dispatcher, self.dispatcher)
        self.assertEqual(broker.component, 'test')
        self.assertEqual(self.dispatcher.brokers, dict(test=dict(callback=None, subscriptions=dict())))

    def test_get_broker_callback(self):
        callback = Callback()
        broker = self.dispatcher.get_broker('test', callback.function)
        self.assertIsInstance(broker, Broker)
        self.assertEqual(broker.dispatcher, self.dispatcher)
        self.assertEqual(broker.component, 'test')
        self.assertEqual(self.dispatcher.brokers, dict(test=dict(callback=callback.function, subscriptions=dict())))


class DispatcherSendTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.log = Logger()
        self.dispatcher = Dispatcher(log=self.log)

    async def test_simple(self):
        callback_1 = Callback()
        callback_2 = Callback()
        callback_3 = Callback()
        broker_1 = self.dispatcher.get_broker('c1', callback_1.function)
        broker_2 = self.dispatcher.get_broker('c2', callback_2.function)
        broker_3 = self.dispatcher.get_broker('c3', callback_3.function)
        await broker_1.send('c2', 'event')
        self.assertEqual(callback_1.called, [])
        self.assertEqual(callback_2.called, [dict(sender='c1', topic='event', payload=None)])
        self.assertEqual(callback_3.called, [])

    async def test_no_callback(self):
        log = Logger(level='debug')
        dispatcher = Dispatcher(log=log)
        broker_1 = dispatcher.get_broker('c1')
        broker_2 = dispatcher.get_broker('c2')
        await broker_1.send('c2', 'command')
        self.assertEqual(log.logged, [('debug', 'No callback - c1 -> c2' )])

    async def test_no_recipient(self):
        log = Logger(level='debug')
        dispatcher = Dispatcher(log=log)
        broker = dispatcher.get_broker('component')
        await broker.send('doesnotexist', 'command')
        self.assertEqual(log.logged, [('debug', 'No recipient - component -> doesnotexist' )])

    async def test_callback_exception(self):
        async def wrong(**kwargs):
            raise Exception
        broker_1 = self.dispatcher.get_broker('c1')
        broker_2 = self.dispatcher.get_broker('c2', wrong)
        await broker_1.send('c2', 'event')
        self.assertEqual(self.log.logged, [('exception', 'Callback error - c1 -> c2')])

    async def test_callback_exception_typeerror(self):
        async def wrong(**kwargs):
            raise TypeError('custom')
        broker_1 = self.dispatcher.get_broker('c1')
        broker_2 = self.dispatcher.get_broker('c2', wrong)
        await broker_1.send('c2', 'event')
        self.assertEqual(self.log.logged, [('exception', 'Callback error - c1 -> c2')])

    async def test_callback_not_async(self):
        def notasync(**kwargs):
            return
        broker_1 = self.dispatcher.get_broker('c1')
        broker_2 = self.dispatcher.get_broker('c2', notasync)
        await broker_1.send('c2', 'event')
        self.assertEqual(self.log.logged, [('error', 'Callback not async - c1 -> c2')])


class DispatcherSubscribeTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.log = Logger()
        self.dispatcher = Dispatcher(log=self.log)

    async def test_everything(self):
        broker = self.dispatcher.get_broker('test')
        callback = Callback()
        await broker.subscribe(callback.function)
        # broker
        subscriptions = self.dispatcher.brokers['test']['subscriptions']
        self.assertEqual(subscriptions, {(None, None): callback.function})
        # dispatcher
        subscriptions = self.dispatcher.subscriptions
        self.assertEqual(subscriptions, {(None, None): dict(test=callback.function)})

    async def test_sender(self):
        broker = self.dispatcher.get_broker('test')
        callback = Callback()
        await broker.subscribe(callback.function, sender='network')
        # broker
        subscriptions = self.dispatcher.brokers['test']['subscriptions']
        self.assertEqual(subscriptions, {('network', None): callback.function})
        # dispatcher
        subscriptions = self.dispatcher.subscriptions
        self.assertEqual(subscriptions, {('network', None): dict(test=callback.function)})

    async def test_topic(self):
        broker = self.dispatcher.get_broker('test')
        callback = Callback()
        await broker.subscribe(callback.function, topic='alert')
        # broker
        subscriptions = self.dispatcher.brokers['test']['subscriptions']
        self.assertEqual(subscriptions, {(None, 'alert'): callback.function})
        # dispatcher
        subscriptions = self.dispatcher.subscriptions
        self.assertEqual(subscriptions, {(None, 'alert'): dict(test=callback.function)})

    async def test_sender_topic(self):
        broker = self.dispatcher.get_broker('test')
        callback = Callback()
        await broker.subscribe(callback.function, sender='network', topic='connect')
        # broker
        subscriptions = self.dispatcher.brokers['test']['subscriptions']
        self.assertEqual(subscriptions, {('network', 'connect'): callback.function})
        # dispatcher
        subscriptions = self.dispatcher.subscriptions
        self.assertEqual(subscriptions, {('network', 'connect'): dict(test=callback.function)})

    async def test_already_subscribed(self):
        broker = self.dispatcher.get_broker('test')
        callback = Callback()
        await broker.subscribe(callback.function, sender='network', topic='connect')
        await broker.subscribe(callback.function, sender='network', topic='disconnect')
        await broker.subscribe(callback.function, sender='network')
        await broker.subscribe(callback.function, sender='mqtt')
        await broker.subscribe(callback.function, topic='online')
        await broker.subscribe(callback.function, topic='offline')
        await broker.subscribe(callback.function)
        self.assertEqual(self.log.logged, [])
        await broker.subscribe(callback.function, sender='network', topic='connect')
        await broker.subscribe(callback.function, sender='network', topic='disconnect')
        await broker.subscribe(callback.function, sender='network')
        await broker.subscribe(callback.function, sender='mqtt')
        await broker.subscribe(callback.function, topic='online')
        await broker.subscribe(callback.function, topic='offline')
        await broker.subscribe(callback.function)
        self.assertEqual(self.log.logged[0], ('error', 'Already subscribed - test -> network connect'))
        self.assertEqual(self.log.logged[1], ('error', 'Already subscribed - test -> network disconnect'))
        self.assertEqual(self.log.logged[2], ('error', 'Already subscribed - test -> network None'))
        self.assertEqual(self.log.logged[3], ('error', 'Already subscribed - test -> mqtt None'))
        self.assertEqual(self.log.logged[4], ('error', 'Already subscribed - test -> None online'))
        self.assertEqual(self.log.logged[5], ('error', 'Already subscribed - test -> None offline'))
        self.assertEqual(self.log.logged[6], ('error', 'Already subscribed - test -> None None'))
        self.assertEqual(len(self.log.logged), 7)


class DispatcherPublishTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.log = Logger()
        self.dispatcher = Dispatcher(log=self.log)
        self.broker = self.dispatcher.get_broker('c')
        self.broker_1 = self.dispatcher.get_broker('c1')
        self.broker_2 = self.dispatcher.get_broker('c2')
        self.broker_3 = self.dispatcher.get_broker('c3')
        self.broker_4 = self.dispatcher.get_broker('c4')
        self.broker_5 = self.dispatcher.get_broker('c5')
        self.callback_1 = Callback()
        self.callback_2 = Callback()
        self.callback_3 = Callback()
        self.callback_4 = Callback()
        self.callback_5 = Callback()

    async def test_no_subcribers(self):
        await self.broker.publish(topic='state', payload='online')

    async def test_subcribe_no_payload(self):
        await self.broker_1.subscribe(self.callback_1.function)
        await self.broker.publish(topic='start')
        self.assertEqual(self.callback_1.called, [dict(sender='c', topic='start', payload=None)])

    async def test_subscribe_everything(self):
        await self.broker_1.subscribe(self.callback_1.function)
        await self.broker.publish(topic='state', payload='online')
        self.assertEqual(self.callback_1.called, [dict(sender='c', topic='state', payload='online')])

    async def test_subscribe_sender(self):
        await self.broker_1.subscribe(self.callback_1.function, sender='c')
        await self.broker_2.subscribe(self.callback_2.function, sender='c1')
        await self.broker.publish(topic='state', payload='online')
        self.assertEqual(self.callback_1.called, [dict(sender='c', topic='state', payload='online')])
        self.assertEqual(self.callback_2.called, [])

    async def test_subscribe_topic(self):
        await self.broker_1.subscribe(self.callback_1.function, topic='state')
        await self.broker_2.subscribe(self.callback_2.function, topic='another')
        await self.broker.publish(topic='state', payload='online')
        self.assertEqual(self.callback_1.called, [dict(sender='c', topic='state', payload='online')])
        self.assertEqual(self.callback_2.called, [])

    async def test_subscribe_sender_topic(self):
        await self.broker_1.subscribe(self.callback_1.function, sender='c', topic='state')
        await self.broker_2.subscribe(self.callback_2.function, sender='c1', topic='state')
        await self.broker_3.subscribe(self.callback_3.function, sender='c', topic='another')
        await self.broker_4.subscribe(self.callback_4.function, sender='c1', topic='another')
        await self.broker.publish(topic='state', payload='online')
        self.assertEqual(self.callback_1.called, [dict(sender='c', topic='state', payload='online')])
        self.assertEqual(self.callback_2.called, [])
        self.assertEqual(self.callback_3.called, [])
        self.assertEqual(self.callback_4.called, [])

    async def test_subscribe_many(self):
        await self.broker_1.subscribe(self.callback_1.function)
        await self.broker_2.subscribe(self.callback_2.function, sender='c')
        await self.broker_3.subscribe(self.callback_3.function, topic='state')
        await self.broker_4.subscribe(self.callback_4.function, sender='c', topic='state')
        await self.broker_5.subscribe(self.callback_5.function, topic='another')
        await self.broker.publish(topic='state', payload='online')
        self.assertEqual(self.callback_1.called, [dict(sender='c', topic='state', payload='online')])
        self.assertEqual(self.callback_2.called, [dict(sender='c', topic='state', payload='online')])
        self.assertEqual(self.callback_3.called, [dict(sender='c', topic='state', payload='online')])
        self.assertEqual(self.callback_4.called, [dict(sender='c', topic='state', payload='online')])
        self.assertEqual(self.callback_5.called, [])

    async def test_callback_exception(self):
        async def wrong(**kwargs):
            raise Exception
        await self.broker_1.subscribe(wrong)
        await self.broker_2.subscribe(self.callback_2.function)
        await self.broker.publish(topic='state', payload='online')
        self.assertEqual(self.log.logged, [('exception', 'Callback error - c1 <- c event')])
        self.assertEqual(self.callback_2.called, [dict(sender='c', topic='state', payload='online')])

    async def test_callback_exception_typeerror(self):
        async def wrong(**kwargs):
            raise TypeError('custom')
        await self.broker_1.subscribe(wrong)
        await self.broker_2.subscribe(self.callback_2.function)
        await self.broker.publish(topic='state', payload='online')
        self.assertEqual(self.log.logged, [('exception', 'Callback error - c1 <- c event')])
        self.assertEqual(self.callback_2.called, [dict(sender='c', topic='state', payload='online')])

    async def test_callback_not_async(self):
        def notasync(**kwargs):
            return
        await self.broker_1.subscribe(notasync)
        await self.broker_2.subscribe(self.callback_2.function)
        await self.broker.publish(topic='state', payload='online')
        self.assertEqual(self.log.logged, [('error', 'Callback not async - c1 <- c event')])
        self.assertEqual(self.callback_2.called, [dict(sender='c', topic='state', payload='online')])
