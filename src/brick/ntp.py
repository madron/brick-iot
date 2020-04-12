import machine
import uasyncio as asyncio
import usocket as socket
import ustruct as struct
import utime
from brick.utils import get_iso_timestamp


class NtpClient:
    def __init__(self, host='pool.ntp.org', timezone=0, delay=86400, ntp_delta=3155673600, log=None, network=None):
        # (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
        self.host = host
        self.timezone = timezone
        self.delay = delay
        self.ntp_delta = ntp_delta
        self.log = log
        self.network = network
        # Task
        self.task = None
        self.loop = asyncio.get_event_loop()

    async def start(self):
        self.log.info('Started')
        self.task = asyncio.create_task(self.start_loop())
        await asyncio.sleep(0)

    async def start_loop(self):
        while True:
            try:
                timestamp = await self.get_time()
                current_timestamp = utime.mktime(utime.localtime())
                await self.set_time(timestamp=timestamp)
                drift = current_timestamp - timestamp
                self.log.info('Host: {}  time: {}  drift: {}'.format(self.host, get_iso_timestamp(timestamp), drift))
                await asyncio.sleep(self.delay)
            except OSError:
                self.log.warning('Fail to connect to {}, Retrying in 5 seconds'.format(self.host))
                await asyncio.sleep(5)
            except Exception as error:
                self.log.exception('Fail to connect to {}, Retrying in {} seconds'.format(self.host, self.delay), error)
                await asyncio.sleep(self.delay)

    async def stop_later(self, delay):
        self.log.info('Stopping in {} seconds'.format(delay))
        asyncio.create_task(self.stop(delay))
        await asyncio.sleep(0)

    async def stop(self, delay=0):
        await asyncio.sleep(delay)
        self.task.cancel()
        await asyncio.sleep(0)
        self.log.info('Stopped')

    async def get_time(self):
        NTP_QUERY = bytearray(48)
        NTP_QUERY[0] = 0x1B
        addr = socket.getaddrinfo(self.host, 123)[0][-1]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.settimeout(1)
            res = s.sendto(NTP_QUERY, addr)
            msg = s.recv(48)
        finally:
            s.close()
        val = struct.unpack("!I", msg[40:44])[0]
        return val + (self.timezone * 3600) - self.ntp_delta

    # There's currently no timezone support in MicroPython, so
    # utime.localtime() will return UTC time (as if it was .gmtime())
    async def set_time(self, timestamp=None):
        timestamp = timestamp or self.get_time()
        tm = utime.localtime(timestamp)
        machine.RTC().init((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
