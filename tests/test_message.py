import unittest
from .test import MessageCallback, Logger
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
        self.assertEqual(self.dispatcher.brokers, dict(test=dict(callback=None, subscriptions=[])))

    def test_get_broker_callback(self):
        callback = MessageCallback()
        broker = self.dispatcher.get_broker('test', callback.function)
        self.assertIsInstance(broker, Broker)
        self.assertEqual(broker.dispatcher, self.dispatcher)
        self.assertEqual(broker.component, 'test')
        self.assertEqual(self.dispatcher.brokers, dict(test=dict(callback=callback.function, subscriptions=[])))

    async def test_send(self):
        callback_1 = MessageCallback()
        callback_2 = MessageCallback()
        callback_3 = MessageCallback()
        broker_1 = self.dispatcher.get_broker('c1', callback_1.function)
        broker_2 = self.dispatcher.get_broker('c2', callback_2.function)
        await broker_1.send('c2', 'event')
        self.assertEqual(callback_1.called, [])
        self.assertEqual(callback_2.called, [dict(sender='c1', topic='event', payload=None)])
        self.assertEqual(callback_3.called, [])

    async def test_send_no_callback(self):
        log = Logger(level='debug')
        dispatcher = Dispatcher(log=log)
        broker_1 = dispatcher.get_broker('c1')
        broker_2 = dispatcher.get_broker('c2')
        await broker_1.send('c2', 'command')
        self.assertEqual(log.logged, [('debug', 'No callback - c1 -> c2' )])

    async def test_send_no_recipient(self):
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
