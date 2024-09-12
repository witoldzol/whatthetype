from random import choice
import sys
from enum import Enum
from foo import example_function, function_taking_nested_class, example_function_with_third_party_lib, function_calling_nested_functions
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
    if obj is None:
        return False
    return isinstance(obj, object) and not isinstance(obj, (int, float, str, list, dict, tuple, set))

def trace_function(frame, event, arg):
    module_name = frame.f_code.co_filename
    func_name = frame.f_code.co_name
    # fiter out non user defined functions
    if PROJECT_NAME not in module_name or func_name == "trace":
        return trace_function
    line_number = frame.f_code.co_firstlineno
    mod_func_line = f"{module_name}:{func_name}:{line_number}"
    function_arg_count = frame.f_code.co_argcount
    function_arg_names = frame.f_code.co_varnames[:function_arg_count]
    local_vars = frame.f_locals
    # create module_function_line entry
    if mod_func_line not in RESULT:
        RESULT[mod_func_line] = {"args": {}}
    ##### CALL #####
    if event == TraceEvent.CALL:
        for name in function_arg_names:
            print(f"Function name => {func_name}")
            print(f"1) function arg name is : {name}")
            # ignore self references
            if name == "self":
                continue
            var = local_vars[name]
            var_type = type(var).__name__
            print(f"2) variable type name is  : {var_type}")
            print(f"----")
            # step 1 || 
            # don't return type, just value, ( unless it's a class - then capture a USER_CLASS|module::name )
            # we don't care about the types at this point, we want values
            # step 2 || we can derive variable types ( this way, if a func arg is called with different var types, we can spot that -> this would be most likely a bug or indication of unreliable inputs )
            if is_user_defined_class(var):
                var = f"USER_CLASS|{var.__module__}::{var_type}"
            if name in RESULT[mod_func_line]["args"]:
                RESULT[mod_func_line]["args"][name].append(var)
            else:
                RESULT[mod_func_line]["args"][name] = [var]
    ##### RETURN #####
    elif event == TraceEvent.RETURN:
        print(f"RETURN : {arg}")
        # return_type = type(arg).__name__
        if "return" in RESULT[mod_func_line]:
            RESULT[mod_func_line]["return"].append(arg)
        else:
            RESULT[mod_func_line]["return"] = [arg]
    return trace_function

def parse_results_to_types(result: dict) -> dict:
    return {}

if __name__ == "__main__":
    sys.settrace(trace_function)
    print("========== TRACING ON ==========")
    example_function(1, 2, None)
    # second type of arg
    example_function("1", 2, None)
    # third party will not get captured
    example_function_with_third_party_lib("1", 2)
    # this will not get captured - it's not user function
    choice(list(range(1,1000)))
    lol = Bar()
    function_taking_nested_class(lol)
    function_calling_nested_functions()
    # class method gets captured
    lol.do_bar(1)
    sys.settrace(None)
    print("========== TRACING OFF ==========")
    print("-"*20, ' RESULT ', "-"*20)
    print(RESULT)
    print("-"*20)
    print("STAGE 1 END")
    print("-"*20)
    print("STAGE 2 START")
    parse_results_to_types(RESULT)
