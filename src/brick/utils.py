import sys
import uio
import utime


def get_iso_timestamp(timestamp=None):
    timestamp = timestamp or utime.time()
    return '{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}'.format(*utime.localtime(timestamp))


def get_traceback(error):
    stream = uio.StringIO()
    sys.print_exception(error, stream)
    return stream.getvalue()


def print_time_diff(start_us, msg):
    print('{} {} microseconds'.format(msg, utime.ticks_diff(utime.ticks_us(), start_us)))
