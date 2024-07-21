import contextlib
import sys
from enum import Enum
from foo import example_function

FUNC_VARIABLES = {}
MODEL = {
    "module:func_name:func_line" : {
        "args": {
            "a" : []
        },
        "return": []
    }
}

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
    module_name =frame.f_code.co_filename
    func_name = frame.f_code.co_name
    line_number = example_function.__code__.co_firstlineno
    mod_func_line = f"{module_name}:{func_name}:{line_number}"
    function_arg_count = frame.f_code.co_argcount
    arg_names = frame.f_code.co_varnames[:function_arg_count]
    local_vars = frame.f_locals
    if PROJECT_NAME not in module_name or func_name == "trace":
        return trace_function
    if mod_func_line not in FUNC_VARIABLES:
        FUNC_VARIABLES[mod_func_line] = {"args":{}}
    print(f"ARG NAMES: {arg_names}")
    if event == TraceEvent.CALL:
        for k in arg_names:
            if k == 'self':
                continue
            var = local_vars[k]
            var_type = type(var).__name__
            if k in FUNC_VARIABLES[mod_func_line]["args"]:
                FUNC_VARIABLES[mod_func_line]["args"][k].append(var_type)
            else:
                FUNC_VARIABLES[mod_func_line]["args"][k] = [var_type]
    elif event == TraceEvent.RETURN:
        print(f"RETURN : {arg}")
        return_type = type(arg).__name__
        if "return" in FUNC_VARIABLES[mod_func_line]:
            FUNC_VARIABLES[mod_func_line]["return"].append(return_type)
        else:
            FUNC_VARIABLES[mod_func_line]["return"] = [return_type]
    print(f"FUNC_VARIABLES :\n {FUNC_VARIABLES}")
    return trace_function

@contextlib.contextmanager
def trace():
    print('tracing on')
    sys.settrace(trace_function)
    yield FUNC_VARIABLES
    print('tracing off')
    sys.settrace(None)

def run():
    with trace():
        result = example_function(1, 2)
        print(FUNC_VARIABLES)

if __name__ == '__main__':
    run()
