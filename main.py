import contextlib
import sys
from enum import Enum
from foo import example_function
from foo import Foo

FUNC_VARIABLES = {}
MODEL = {
    "module:func_name:func_line": {
        "args": {
            "var_name": set('type')
        }, "return": set('type')
    }
}

PROJECT_NAME = "typemedaddy"


class TraceEvent(Enum):
    CALL = "call"  #: Triggered when a function is called.
    LINE = "line"  #: Triggered when a new line of code is executed.
    RETURN = "return"  #: Triggered when a function is about to return.
    EXCEPTION = "exception"  #: Triggered when an exception is raised.

    # if string, compare to value by default
    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)

def is_user_defined_class(obj):
    return isinstance(obj, object) and not isinstance(obj, (int, float, str, list, dict, tuple, set))

def trace_function(frame, event, arg):
    module_name = frame.f_code.co_filename
    func_name = frame.f_code.co_name
    line_number = example_function.__code__.co_firstlineno
    mod_func_line = f"{module_name}:{func_name}:{line_number}"
    function_arg_count = frame.f_code.co_argcount
    arg_names = frame.f_code.co_varnames[:function_arg_count]
    local_vars = frame.f_locals
    if PROJECT_NAME not in module_name or func_name == "trace":
        return trace_function
    if mod_func_line not in FUNC_VARIABLES:
        FUNC_VARIABLES[mod_func_line] = {"args": {}}
    print(f"ARG NAMES: {arg_names}")
    if event == TraceEvent.CALL:
        for name in arg_names:
            # ignore self references
            if name == "self":
                continue
            var = local_vars[name]
            var_type = type(var).__name__
            # don't return type, just value, ( unless it's a class - then capture a name )
            if is_user_defined_class(var):
                print("USER CLASS ======================")
                print("VAR TYPE === ", var_type)
                print(var)
            else:
                print("not a class ", var_type)

            if name in FUNC_VARIABLES[mod_func_line]["args"]:
                FUNC_VARIABLES[mod_func_line]["args"][name].add(var_type)
            else:
                FUNC_VARIABLES[mod_func_line]["args"][name] = set([var_type])
    elif event == TraceEvent.RETURN:
        print(f"RETURN : {arg}")
        return_type = type(arg).__name__
        if "return" in FUNC_VARIABLES[mod_func_line]:
            FUNC_VARIABLES[mod_func_line]["return"].add(return_type)
        else:
            FUNC_VARIABLES[mod_func_line]["return"] = set([return_type])
    print(f"FUNC_VARIABLES :\n {FUNC_VARIABLES}")
    return trace_function

def trace_function_bak(frame, event, arg):
    module_name = frame.f_code.co_filename
    func_name = frame.f_code.co_name
    line_number = example_function.__code__.co_firstlineno
    mod_func_line = f"{module_name}:{func_name}:{line_number}"
    function_arg_count = frame.f_code.co_argcount
    arg_names = frame.f_code.co_varnames[:function_arg_count]
    local_vars = frame.f_locals
    if PROJECT_NAME not in module_name or func_name == "trace":
        return trace_function
    if mod_func_line not in FUNC_VARIABLES:
        FUNC_VARIABLES[mod_func_line] = {"args": {}}
    print(f"ARG NAMES: {arg_names}")
    if event == TraceEvent.CALL:
        for name in arg_names:
            if name == "self":
                continue
            var = local_vars[name]
            var_type = type(var).__name__
            if name in FUNC_VARIABLES[mod_func_line]["args"]:
                FUNC_VARIABLES[mod_func_line]["args"][name].add(var_type)
            else:
                FUNC_VARIABLES[mod_func_line]["args"][name] = set([var_type])
    elif event == TraceEvent.RETURN:
        print(f"RETURN : {arg}")
        return_type = type(arg).__name__
        if "return" in FUNC_VARIABLES[mod_func_line]:
            FUNC_VARIABLES[mod_func_line]["return"].add(return_type)
        else:
            FUNC_VARIABLES[mod_func_line]["return"] = set([return_type])
    print(f"FUNC_VARIABLES :\n {FUNC_VARIABLES}")
    return trace_function


@contextlib.contextmanager
def trace():
    global FUNC_VARIABLES
    print("========== TRACING ON ==========")
    sys.settrace(trace_function)
    try:
        yield FUNC_VARIABLES
    finally:
        print("========== TRACING OFF ==========")
        sys.settrace(None)
        FUNC_VARIABLES = {}


def run():
    with trace():
        f = Foo("bar")
        result = example_function(1, 2, f)
        print(FUNC_VARIABLES)


if __name__ == "__main__":
    run()
