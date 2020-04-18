import io
import sys


def get_traceback(error):
    stream = uio.StringIO()
    sys.print_exception(error, stream)
    return stream.getvalue()
