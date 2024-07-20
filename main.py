import contextlib
import pudb
import sys
from enum import Enum
a = {
    "module:func_name:func_line" : {
        "args": {
            "a" : []
        },
        "returns": []
    }
}

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
        line_number = example_function.__code__.co_firstlineno
        mod_func_line = f"{module_name}:{func_name}:{line_number}"
        local_vars = frame.f_locals
        if PROJECT_NAME not in module_name or func_name == "trace":
            return trace_function
        # if module_name not in FUNC_VARIABLES:
        #     FUNC_VARIABLES[module_name] = {}
        # if func_name not in FUNC_VARIABLES[module_name]:
        #     FUNC_VARIABLES[module_name][func_name] = {}
        if mod_func_line not in FUNC_VARIABLES:
            FUNC_VARIABLES[mod_func_line] = {"args":{}}
        for k, v in local_vars.items():
            if k in FUNC_VARIABLES[mod_func_line]["args"]:
                FUNC_VARIABLES[mod_func_line]["args"][k].append(v)
            else:
                FUNC_VARIABLES[mod_func_line]["args"][k] = [v]

    if event == TraceEvent.RETURN:
        module_name =frame.f_code.co_filename
        func_name = frame.f_code.co_name
        line_number = example_function.__code__.co_firstlineno
        print(module_name)
        print(line_number)
        print(func_name)
        print(f"return value: {arg}")
        
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

