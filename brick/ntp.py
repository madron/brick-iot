import asyncio
import socket
import struct
import time
from asyncio.streams import StreamReader


class NtpClient:
    def __init__(self, host='pool.ntp.org', timezone_callback=None, ntp_delta=3155673600):
        # (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
        self.host = host
        self.timezone_callback = timezone_callback
        self.ntp_delta = ntp_delta

    async def get_time(self):
        NTP_QUERY = bytearray(48)
        NTP_QUERY[0] = 0x1B
        addr = socket.getaddrinfo(self.host, 123)[0][-1]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setblocking(False)
        stream = StreamReader(s)
        try:
            s.sendto(NTP_QUERY, addr)
            msg = await stream.read(48)
        finally:
            await stream.wait_closed()
        val = struct.unpack("!I", msg[40:44])[0] - self.ntp_delta
        if self.timezone_callback:
            val = self.timezone_callback(val)
        return val

    # There's currently no timezone support in MicroPython, so
    # utime.localtime() will return UTC time (as if it was .gmtime())
    async def set_time(self, timestamp=None):
        timestamp = timestamp or await self.get_time()
        tm = utime.localtime(timestamp)
        machine.RTC().init((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))


class NtpSync:
    def __init__(self, log, broker, config, timezone=0, delay=86400, fail_delay=10):
        self.config = config
        self.host = self.config.get('host', 'pool.ntp.org')
        self.ntp_client = NtpClient(host=self.host, timezone_callback=self.timezone_callback)
        self.timezone = timezone
        self.delay = delay
        self.fail_delay = fail_delay
        self.log = log
        self.broker = broker
        # Task
        self.task = None
        self.loop = asyncio.get_event_loop()

    def timezone_callback(self, timestamp):
        return timestamp + (self.timezone * 3600)

    async def start(self, **kwargs):
        self.log.info('Started. Host: {} - delay: {}'.format(self.host, self.delay))
        self.task = asyncio.create_task(self.start_loop())
        await asyncio.sleep(0)

    async def start_loop(self):
        while True:
            try:
                timestamp = await self.ntp_client.get_time()
                current_timestamp = utime.mktime(utime.localtime())
                await self.ntp_client.set_time(timestamp=timestamp)
                self.log.info('Sync successful. Drift: {}'.format(current_timestamp - timestamp))
                await asyncio.sleep(self.delay)
            except OSError as error:
                self.log.warning('Fail to connect to {} (OSError {}), Retrying in {} seconds'.format(self.host, error.args[0], self.fail_delay))
                await asyncio.sleep(self.fail_delay)
            except Exception as error:
                self.log.exception('Fail to connect to {}, Retrying in {} seconds'.format(self.host, self.delay), error)
                await asyncio.sleep(self.delay)

    async def stop_later(self, delay):
        self.log.info('Stopping in {} seconds'.format(delay))
        asyncio.create_task(self.stop(delay))
        await asyncio.sleep(0)

    async def stop(self, delay=0, **kwargs):
        await asyncio.sleep(delay)
        self.task.cancel()
        await asyncio.sleep(0)
        self.log.info('Stopped')
