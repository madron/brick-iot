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
