import asyncio
import functools
import uvicorn
from fastapi import FastAPI
from .root import routes


class ServerState:
    def __init__(self):
        self.total_requests = 0
        self.connections = set()
        self.tasks = set()
        self.default_headers = []


class App(FastAPI):
    def __init__(self, config_manager):
        super().__init__(routes=routes)
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
        # Uvicorn
        self.uvicorn_server = None
        config = uvicorn.Config(
            App(config_manager=self.config_manager),
            log_config=self.get_log_config(),
            use_colors=False
        )
        config.load()
        self.protocol_factory = functools.partial(
            config.http_protocol_class,
            config=config,
            server_state=ServerState(),
        )

    def get_log_config(self):
        config = dict(
            version=1,
            disable_existing_loggers=False,
            formatters=dict(
                default={
                    'class': 'logging.Formatter',
                    'fmt': '%(message)s',
                },
                access={
                    'class': 'logging.Formatter',
                    'fmt': '%(client_addr)s - "%(request_line)s" %(status_code)s',
                },
            ),
            handlers=dict(
                default={
                    'formatter': 'default',
                    'class': 'brick.logging.Logger',
                    'log_collector': self.log_collector,
                    'component': 'web',
                },
                access={
                    'formatter': 'access',
                    'class': 'brick.logging.Logger',
                    'log_collector': self.log_collector,
                    'component': 'web',
                },
            ),
            loggers={
                "": {"handlers": ["default"], "level": "INFO"},
                "uvicorn.error": {"level": "INFO"},
                "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
            },
        )
        return config

    async def start(self, logger=None):
        loop = asyncio.get_event_loop()
        self.uvicorn_server = await loop.create_server(
            self.protocol_factory,
            host=self.host,
            port=self.port,
        )
        self.log.info('Server listening to {}:{}'.format(self.host, self.port))

    async def stop(self, logger=None):
        self.uvicorn_server.close()
        await self.uvicorn_server.wait_closed()
