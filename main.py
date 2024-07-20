import contextlib
import pudb
import sys
from enum import Enum

class TraceEvent(Enum):
    CALL='call' #: Triggered when a function is called.
    LINE='line' #: Triggered when a new line of code is executed.
    RETURN='return' #: Triggered when a function is about to return.
    EXCEPTION='exception' #: Triggered when an exception is raised.

    # if string, compare to value by default
    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)

def trace_function(frame, event, arg):
    # print(f"{frame=}")
    if event == TraceEvent.CALL:
        print(f"{event=}")
        print("Function name:", frame.f_code.co_name)
        print("Local variables:", frame.f_locals)
    # print("Global variables:", list(frame.f_globals.keys()))
    return trace_function

def example_function(a, b):
    c = a + b
    return c

@contextlib.contextmanager
def trace():
    print('tracing on')
    sys.settrace(trace_function)
    yield
    print('tracing off')
    sys.settrace(None)

with trace():
    result = example_function(1, 2)
    print(result)
