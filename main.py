import contextlib
import sys
from enum import Enum
from foo import example_function, function_taking_nested_class
from foo import Foo
from nested.inner.bar import Bar

RESULT = {}
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
    function_arg_names = frame.f_code.co_varnames[:function_arg_count]
    local_vars = frame.f_locals
    if PROJECT_NAME not in module_name or func_name == "trace":
        return trace_function
    # setup dictionary
    if mod_func_line not in RESULT:
        RESULT[mod_func_line] = {"args": {}}
    ##### CALL #####
    if event == TraceEvent.CALL:
        for name in function_arg_names:
            print(f"1) function arg name is : {name}")
            # ignore self references
            if name == "self":
                continue
            var = local_vars[name]
            var_type = type(var).__name__
            print(f"2) variable type name is  : {var_type}")
            # don't return type, just value, ( unless it's a class - then capture a name )
            print(f"MODULE ======================> {var.__class__.__module__}")
            if is_user_defined_class(var):
                print("USER CLASS ======================")
                print("VAR TYPE => ", var_type, "\nVAR VALUE ==> ", var)
            else:
                print("not a class ", var_type)
            if name in RESULT[mod_func_line]["args"]:
                RESULT[mod_func_line]["args"][name].add(var_type)
            else:
                RESULT[mod_func_line]["args"][name] = set([var_type])
    ##### RETURN #####
    elif event == TraceEvent.RETURN:
        print(f"RETURN : {arg}")
        return_type = type(arg).__name__
        if "return" in RESULT[mod_func_line]:
            RESULT[mod_func_line]["return"].add(return_type)
        else:
            RESULT[mod_func_line]["return"] = set([return_type])
    print(f"FUNC_VARIABLES :\n {RESULT}")
    return trace_function

@contextlib.contextmanager
def trace():
    global RESULT
    print("========== TRACING ON ==========")
    sys.settrace(trace_function)
    try:
        yield RESULT
    finally:
        print("========== TRACING OFF ==========")
        sys.settrace(None)
        RESULT = {}


if __name__ == "__main__":
    with trace():
        # f = Foo("bar")
        # result = example_function(1, 2, f)
        lol = Bar()

        bar_name = function_taking_nested_class(lol)
        print(RESULT)
