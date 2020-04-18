import asyncio
import time


class NetworkManager:
    def __init__(self, log, broker, config=dict()):
        self.log = log
        self.broker = broker

    async def start(self, delay=0):
        await asyncio.sleep(0)

    async def stop(self, delay=0):
        await asyncio.sleep(0)
