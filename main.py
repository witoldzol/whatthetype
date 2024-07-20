import contextlib
import pudb
import sys
from enum import Enum

FUNC_VARIABLES = {}
PROJECT_NAME="typemedaddy"

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
    if event == TraceEvent.CALL:
        module_name =frame.f_code.co_filename
        func_name = frame.f_code.co_name
        if PROJECT_NAME not in module_name or func_name == "trace":
            return trace_function
        local_vars = frame.f_locals
        if module_name not in FUNC_VARIABLES:
            FUNC_VARIABLES[module_name] = {}
        if func_name not in FUNC_VARIABLES[module_name]:
            FUNC_VARIABLES[module_name][func_name] = {}
        for k, v in local_vars.items():
            FUNC_VARIABLES[module_name][func_name][k] = v
        # print("Function name:", func_name)
        # print(f"Function module: {module}")
        # print("Local variables:", local_vars)
        
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
    print(FUNC_VARIABLES)

