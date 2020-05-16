import asyncio
import functools
import uvicorn
from fastapi import FastAPI


app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


class ServerState:
    def __init__(self):
        self.total_requests = 0
        self.connections = set()
        self.tasks = set()
        self.default_headers = []


class Server:
    def __init__(self, log_collector, broker, config=dict()):
        self.log_collector = log_collector
        self.broker = broker
        self.config = config
        self.log = self.log_collector.get_logger('web')
        self.host = config.get('host', '0.0.0.0')
        self.port = config.get('port', 80)
        self.port = 8000
        # Uvicorn
        self.uvicorn_server = None
        config = uvicorn.Config(app)
        config.load()
        self.protocol_factory = functools.partial(
            config.http_protocol_class,
            config=config,
            server_state=ServerState(),
        )

    async def start(self, logger=None):
        loop = asyncio.get_event_loop()
        self.uvicorn_server = await loop.create_server(
            self.protocol_factory,
            host=self.host,
            port=self.port,
        )
        self.log.info('Server started on port {}'.format(self.port))

    async def stop(self, logger=None):
        self.uvicorn_server.close()
        await self.uvicorn_server.wait_closed()
