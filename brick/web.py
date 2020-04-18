import asyncio


class Server:
    def __init__(self, log_collector, config=dict()):
        self.log_collector = log_collector
        self.config = config
        self.log = self.log_collector.get_logger('web')
        self.port = config.get('port', 80)
        self.task = None

    async def start(self, logger=None):
        self.task = asyncio.create_task(asyncio.sleep(0))
        self.log.info('TO BE IMPLENTED Server started on port {}'.format(self.port))

    async def stop(self, logger=None):
        self.task.cancel()
