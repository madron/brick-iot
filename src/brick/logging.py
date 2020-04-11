import sys
import uasyncio as asyncio
from uuid import uuid4
from brick.utils import get_iso_timestamp, get_traceback


CRITICAL = 50
ERROR    = 40
WARNING  = 30
INFO     = 20
DEBUG    = 10
NOTSET   = 100

LEVEL_NUMBER = dict(
    critical=CRITICAL,
    error=ERROR,
    warning=WARNING,
    info=INFO,
    debug=DEBUG,
)
LEVEL_NAME = {
    CRITICAL: 'critical',
    ERROR: 'error',
    WARNING: 'warning',
    INFO: 'info',
    DEBUG: 'debug',
}


class Logger:
    def __init__(self, log_collector, component):
        self.log_collector = log_collector
        self.component = component

    def log(self, level, message, *args, **kwargs):
        self.log_collector.log(level, self.component, message, *args, **kwargs)

    def debug(self, message, *args, **kwargs):
        self.log(DEBUG, message, *args)

    def info(self, message, *args, **kwargs):
        self.log(INFO, message, *args)

    def warning(self, message, *args, **kwargs):
        self.log(WARNING, message, *args)

    def error(self, message, *args, **kwargs):
        self.log(ERROR, message, *args)

    def critical(self, message, *args, **kwargs):
        self.log(CRITICAL, message, *args)

    def exception(self, message, error, *args, **kwargs):
        traceback = get_traceback(error)
        self.log(ERROR, message, *args)
        self.log(ERROR, traceback, *args)


class LogCollector:
    def __init__(self):
        self.consumers = dict()
        self.loop = asyncio.get_event_loop()

    def log(self, level, component, message, *args, **kwargs):
        for consumer in self.consumers.values():
            if level >= consumer['components'].get(component, consumer['level']):
                self.loop.create_task(consumer['callback'](level, component, message, *args, **kwargs))

    def get_logger(self, component):
        return Logger(self, component)

    def add_consumer(self, callback, level='info', components=dict()):
        consumer_id = uuid4()
        self.consumers[consumer_id] = dict(
            callback=callback,
            level=LEVEL_NUMBER.get(level, NOTSET),
            components=dict([(x[0], LEVEL_NUMBER.get(x[1], NOTSET)) for x in components.items()])
        )
        return consumer_id

    def remove_consumer(self, consumer_id):
        return self.consumers.pop(consumer_id, None)


class StdoutLogConsumer:
    def __init__(self, log_collector, level='info', components=dict()):
        log_collector.add_consumer(self.log, level=level, components=components)

    async def log(self, level, component, message, *args, **kwargs):
        sys.stdout.write('{} {:8s} {}: {}\n'.format(
            get_iso_timestamp(),
            LEVEL_NAME[level].upper(),
            component,
            message,
        ))
