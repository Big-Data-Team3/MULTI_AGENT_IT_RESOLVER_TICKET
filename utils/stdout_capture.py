import io
import sys
from contextlib import redirect_stdout

def capture_output(func, *args, **kwargs):
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        result = func(*args, **kwargs)
    logs = buffer.getvalue()
    return result, logs
