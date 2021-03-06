import asyncio
import unittest


class Callback:
    def __init__(self, delay=0):
        self.delay = delay
        self.called = []

    async def function(self, sender=None, topic=None, payload=None):
        await asyncio.sleep(self.delay)
        self.called.append(dict(sender=sender, topic=topic, payload=payload))


class Logger:
    level_order = dict(
        debug=10,
        info=20,
        warning=30,
        error=40,
        exception=50,
    )
    def __init__(self, level='info'):
        self.level = level
        self.logged = []

    def append(self, msg, type):
        if self.level_order[type] >= self.level_order[self.level]:
            self.logged.append((type, msg))

    def debug(self, msg):
        self.append(msg, 'debug')

    def info(self, msg):
        self.append(msg, 'info')

    def warning(self, msg):
        self.append(msg, 'warning')

    def error(self, msg):
        self.append(msg, 'error')

    def exception(self, msg, error):
        self.append(msg, 'exception')
