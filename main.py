import contextlib
from random import choice
import sys
from enum import Enum
from foo import (
    returns_a_class,
    example_function,
    function_taking_nested_class,
    example_function_with_third_party_lib,
    function_calling_nested_functions,
)
from nested.inner.bar import Bar

RESULT = {}
MODEL = {
    "module:func_name:func_line": {
        "args": {"var_name": set("type")},
        "return": set("type"),
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
    return isinstance(obj, object) and not isinstance(
        obj, (int, float, str, list, dict, tuple, set)
    )


# we use context for easy testing, same with the RESULT yields, for tests only
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
            # ignore self references
            if name == "self":
                continue
            print(f"Function name => {func_name}")
            print(f"1) function arg name is : {name}")
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
        # return_type = type(arg).__name__
        if is_user_defined_class(arg):
            arg = f"USER_CLASS|{arg.__module__}::{type(arg).__name__}"
        if "return" in RESULT[mod_func_line]:
            RESULT[mod_func_line]["return"].append(arg)
        else:
            RESULT[mod_func_line]["return"] = [arg]
    return trace_function

def figure_out_content_type(input: list) -> str:
    return type(input).__name__

# TODO
# we probably want to throw some warning saying:
# HEY,this func gets different types at various types,
# maybe you should look into this
# INPUT
# {
#   "module_func_line" : {
#       "args":{
#           "name_of_argument": [value,value,...], < this is where we need to use recursion
#           ...,
#           ....
#       },
#       "return": [value, value, ...] < same here, recurse each value
#   } 
# }

def figure_out_the_value_type(value):
    var_type_name = type(value).__name__
    if var_type_name  in ('list'):
        list_content_type = figure_out_content_type(value[0]) if value else '' # todo - hardcoded
        if  list_content_type:
            var_type_name = f"{var_type_name}[{list_content_type}]"
            # if list is empty, just return list type, without brackets
        else:
            var_type_name = f"{var_type_name}"
    return var_type_name 

def convert_results_to_types(input: dict[str,dict]) -> dict:
    if not input:
        return {}
    r = {}
    for mfl in input: # mfl -> module_function_line
        # ========== ARGS ==========
        r[mfl] = {"args": dict()} # init result
        for arg in input[mfl]["args"]:
            r[mfl]["args"][arg] = list() # init result
            for value in input[mfl]["args"][arg]:
                var_type_name = figure_out_the_value_type(value)
                r[mfl]["args"][arg].append(var_type_name)
        # ========== RETURN ==========
        r[mfl]["return"] = list() # init result
        for value in input[mfl]["return"]:
            var_type_name = figure_out_the_value_type(value)
            r[mfl]["return"].append(var_type_name)
    return r


if __name__ == "__main__":
    # ===== STAGE 1 START =====
    with trace():
        pass
        # returns_a_class()
        # example_function(1, 2, None)
        # # second type of arg
        # example_function("1", 2, None)
        # # third party will not get captured
        # example_function_with_third_party_lib("1", 2)
        # # this will not get captured - it's not user function
        # choice(list(range(1, 1000)))
        # lol = Bar()
        # function_taking_nested_class(lol)
        # function_calling_nested_functions()
        # # class method gets captured
        # lol.do_bar(1)
        print("-" * 20, " RESULT: ", "-" * 20)
        print(RESULT)
    print("-" * 20)
    print("STAGE 1 END")
    print("-" * 20)
    # ===== STAGE 2 START =====
    convert_results_to_types(RESULT)
