import asyncio
import functools
import os
import signal
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.routing import APIRoute
from hypercorn.asyncio import serve
from hypercorn.config import Config
from starlette.routing import Mount
from . import root


class App(FastAPI):
    def __init__(self, config_manager):
        module_path = os.path.dirname(os.path.realpath(__file__))
        super().__init__(routes=[
            APIRoute('/', root.home),
            APIRoute('/config', root.config, methods=['GET', 'POST']),
            Mount('/static', StaticFiles(directory=os.path.join(module_path, 'static')), name='static'),
        ])
        self.templates = Jinja2Templates(directory=os.path.join(module_path, 'templates'))
        self.config_manager = config_manager


class Server:
    def __init__(self, log_collector, broker, config_manager, config=dict()):
        self.log_collector = log_collector
        self.broker = broker
        self.config_manager = config_manager
        self.config = config
        self.log = self.log_collector.get_logger('web')
        self.host = config.get('host', '0.0.0.0')
        self.port = config.get('port', 80)
        # Hypercorn
        self.task = None
        self.shutdown_event = asyncio.Event()
        self.hypercorn_config = Config()
        self.hypercorn_config.bind = ['{}:{}'.format(self.host, self.port)]
        self.hypercorn_config.logconfig_dict = self.get_log_config()
        self.app = App(config_manager=self.config_manager)

    def shutdown_signal_handler(self, *args) -> None:
            self.shutdown_event.set()

    def get_log_config(self):
        config = dict(
            version=1,
            disable_existing_loggers=False,
            root=dict(level='INFO', handlers=['default']),
            loggers={
                'hypercorn.error': dict(
                    level='INFO',
                    handlers=['default'],
                    propagate=False,
                    qualname='hypercorn.error',
                ),
                'hypercorn.access': dict(
                    level='INFO',
                    handlers=['default'],
                    propagate=False,
                    qualname='hypercorn.access',
                ),
            },
            handlers=dict(
                default={
                    'formatter': 'default',
                    'class': 'brick.logging.Logger',
                    'log_collector': self.log_collector,
                    'component': 'web',
                },
            ),
            formatters=dict(
                default={
                    'class': 'logging.Formatter',
                    'fmt': '%(message)s',
                },
            ),
        )
        return config

    async def start(self, logger=None):
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGTERM, self.shutdown_signal_handler)
        self.task = asyncio.create_task(
            serve(
                self.app,
                self.hypercorn_config,
                shutdown_trigger=self.shutdown_event.wait,
            )
        )
        self.log.info('Server listening to {}:{}'.format(self.host, self.port))

    async def stop(self, logger=None):
        self.task.cancel()
