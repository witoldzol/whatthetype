import io
from tokenize import INDENT, tokenize, untokenize, NUMBER, STRING, NAME, OP, generate_tokens
import pprint
import logging
import contextlib
from typing import Any
import sys
import os
from enum import Enum
import argparse
from typemedaddy.foo import example_function_with_third_party_lib, Foo
from types import FrameType
from typing import Literal

# take logger args, if we are running directly
# ( this bit was executing when running tests, so I put it in a conditional)
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default="WARNING")
    args = parser.parse_args()
    log_level = args.log.upper()
    if log_level in ("DEBUG", "INFO", "WARNING", "ERROR"):
        logging.basicConfig(level=log_level)
    else:
        logging.basicConfig(level="WARNING")
LOG = logging.getLogger(__name__)

# constants
COLLECTIONS = ("dict", "list", "set", "tuple")
COLLECTIONS_NO_DICT = ("list", "set", "tuple")
SELF_OR_CLS = "SELF_OR_CLS"

RESULT = {}
MODEL = {
    "module:func_name:func_line": {
        "args": {"var_name": set("type")},
        "return": set("type"),
    }
}

# we use `current_folder` to identify local execution dir
# this will be used to filter out non local / non user packages
# so that we don't trace them
# in other words - we don't want to trace functions defined in external libraries, just our own code
PROJECT_NAME = os.getcwd()


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


def is_class_method(func_name: str, frame: FrameType) -> bool:
    # we have access to globals()
    # if function is a class method, it will NOT be listed in gloals()
    # so let's just use that as a check  ->
    #   ( I don't understand internals so this is a quick hack -> let's hope I didn't miss something important )
    return func_name not in frame.f_globals


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
    ################
    ##### CALL #####
    ################
    if event == TraceEvent.CALL:
        # we need to figure out if the called function is a 'free' or is a class method
        # why?
        #   because if it's a class method, first arg will be 'self' or 'cls' ->
        #   but we can't rely on neme or the arg, because it can be anything
        for idx, arg_name in enumerate(function_arg_names):
            # we check index, because self ref object can only be the first arg!
            # if the arg is not firs, then it cannot be a self or cls
            if is_class_method(func_name, frame) and idx == 0:
                var = SELF_OR_CLS
            else:
                LOG.debug(f"1) Function name => {func_name}")
                LOG.debug(f"2) Function arg name is : {arg_name}")
                var = local_vars[arg_name]
                var_type = type(var).__name__
                LOG.debug(f"3) Variable type name is  : {var_type}")
                LOG.debug(f"--- end ---")
                if is_user_defined_class(var):
                    var = f"USER_CLASS|{var.__module__}::{var_type}"
            if arg_name in RESULT[mod_func_line]["args"]:
                RESULT[mod_func_line]["args"][arg_name].append(var)
            else:
                RESULT[mod_func_line]["args"][arg_name] = [var]
    ##################
    ##### RETURN #####
    ##################
    elif event == TraceEvent.RETURN:
        if is_user_defined_class(arg):
            arg = f"USER_CLASS|{arg.__module__}::{type(arg).__name__}"
        if "return" in RESULT[mod_func_line]:
            RESULT[mod_func_line]["return"].append(arg)
        else:
            RESULT[mod_func_line]["return"] = [arg]
    return trace_function


def sort_types_none_at_the_end(set_of_types: set) -> list:
    sorted_types: list = sorted(set_of_types)
    if "None" in sorted_types:
        sorted_types.remove("None")
        sorted_types = sorted_types
        sorted_types.append("None")
    return sorted_types

def get_value_type(val: Any) -> str:
    # type(None) -> NoneType, which we don't really want, because type hint 
    # system uses None string, not NoneType
    if val == None:
        return  'None'
    else:
        return type(val).__name__

# def unify_types(types: list[str]) -> list[str]:
#     pass
#
def convert_value_to_type2(value: Any) -> tuple[Literal["dict", "tuple", "list", "set", "self", "simple"], list]:
    input_type = get_value_type(value)
    # base case
    if input_type not in COLLECTIONS:
        # hardcoded - special case - self reference arg in methods
        if value == SELF_OR_CLS:
            return ('self', [value])
        else:
            return ('simple', [input_type])
    if input_type == "dict":
        types_found_in_collection = set()
        for k, v in value.items():
            key_type = get_value_type(k)
            dict_value_type = get_value_type(v)
            # collections are not hashable, so they will never be collections
            if dict_value_type in COLLECTIONS:
                types_found_in_collection.add(f"{key_type},{convert_value_to_type2(v)}")
            else:
                types_found_in_collection.add(f"{key_type},{dict_value_type}")
        if types_found_in_collection:
            sorted_types = sort_types_none_at_the_end(types_found_in_collection)
            # input_type = f"{input_type}[{'|'.join(sorted_types)}]"
            input_type = (input_type, sorted_types)
            # f"{input_type}[{'|'.join(sorted_types)}]"
        else:
            input_type = (input_type, [])
    elif input_type in COLLECTIONS_NO_DICT:
        types_found_in_collection = set()
        for v in value:
            t = get_value_type(v)
            if t in COLLECTIONS:
                types_found_in_collection.add(convert_value_to_type2(v))
            else:
                types_found_in_collection.add(t)
        if types_found_in_collection:
            sorted_types = sort_types_none_at_the_end(types_found_in_collection)
            input_type = (input_type, sorted_types)
        else:
            input_type = (input_type, [])
    else:
        raise Exception(f'Unexpected type : {input_type}')
    return input_type

def convert_value_to_type(value: Any) -> str:
    input_type = get_value_type(value)
    # base case
    if input_type not in COLLECTIONS:
        # hardcoded - special case - self reference arg in methods
        if value == SELF_OR_CLS:
            return value
        else:
            return input_type
    if input_type == "dict":
        types_found_in_collection = set()
        for k, v in value.items():
            key_type = get_value_type(k)
            dict_value_type = get_value_type(v)
            # collections are not hashable, so they will never be collections
            if dict_value_type in COLLECTIONS:
                types_found_in_collection.add(f"{key_type},{convert_value_to_type(v)}")
            else:
                types_found_in_collection.add(f"{key_type},{dict_value_type}")
        if types_found_in_collection:
            sorted_types = sort_types_none_at_the_end(types_found_in_collection)
            pop_top_type(sorted_types)
            input_type = f"{input_type}[{'|'.join(sorted_types)}]"
    elif input_type in COLLECTIONS_NO_DICT:
        types_found_in_collection = set()
        for v in value:
            t = get_value_type(v)
            if t in COLLECTIONS:
                types_found_in_collection.add(convert_value_to_type(v))
            else:
                types_found_in_collection.add(t)
        if types_found_in_collection:
            sorted_types = sort_types_none_at_the_end(types_found_in_collection)
            input_type = f"{input_type}[{'|'.join(sorted_types)}]"
    return input_type


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
def convert_results_to_types(input: dict[str, dict]) -> dict:
    if not input:
        return {}
    result = {}
    # mfl => module_function_line
    for mfl in input:
        # ========== ARGS ==========
        result[mfl] = {"args": dict()}  # init result
        for arg in input[mfl]["args"]:
            # lets use set to de-dup types
            s = set()
            result[mfl]["args"][arg] = list()  # init result
            # iterate over function's every arguemnt, and it's values
            for value in input[mfl]["args"][arg]:
                var_type_name = convert_value_to_type(value)
                s.add(var_type_name)
            # we sort the output, to get deterministic results -> set has random ordering
            # TODO this returns array of types, which we will have to collapse again?
            result[mfl]["args"][arg] = sorted(list(s))
        # ========== RETURN ==========
        result[mfl]["return"] = list()
        # lets use set to de-dup types
        s = set()
        for value in input[mfl]["return"]:
            var_type_name = convert_value_to_type(value)
            s.add(var_type_name)
            # we sort the output, to get deterministic results -> set has random ordering
        result[mfl]["return"] = sorted(list(s))
    return result

def update_code_with_types(data: dict) -> dict[str, object]:
    updated_function_declarations = dict()
    for mfl in data.keys():
        new_module = []
        module, function, line_num = mfl.split(":") # edge case, if file or func has a ':' in a name
        with open(module, "r") as f:
            for idx, line in enumerate(f):
                # find a line containting the function
                if idx == int(line_num) - 1:
                    # convert line to StringIO - required by tokenizer
                    line_io = io.StringIO(line).readline # don't use lambda, generator will be infinite
                    # get tokens
                    tokens = generate_tokens(line_io)
                    """ sample tokenizer output [ first line full, rest truncated ]
                    TokenInfo(type=5 (INDENT), string='    ', start=(1, 0), end=(1, 4), line="    def arbitrary_self(not_self, name: str = 'default_val', age=10):\n")
                    TokenInfo(type=1 (NAME), string='def', _, _, _ ...
                    TokenInfo(type=1 (NAME), string='arbitrary_self', _, _, _ ...
                    TokenInfo(type=55 (OP), string='(', _, _, _ ...
                    TokenInfo(type=1 (NAME), string='not_self', _, _, _ ...
                    TokenInfo(type=55 (OP), string=',', _, _, _ ...
                    TokenInfo(type=1 (NAME), string='name', _, _, _ ...
                    TokenInfo(type=55 (OP), string=':', _, _, _ ...
                    ...
                    """
                    # do the magic
                    result = []
                    in_arguments = False
                    # untokenize will not handle spacing and indentation if we remove last 3 args
                    # so we have to handle it manually
                    indentation = []
                    type_detected = False
                    for t in tokens:
                        # we care only about first 2 values, type is a number mapped in an ENUM
                        token_type, token_val, _, _, _ = t
                        # start of arguments
                        if token_type == OP and token_val == '(':
                            in_arguments = True
                            print("ARGUMENTS START ->>>>")
                            result.append((token_type, token_val,))
                        # end of arguments
                        elif token_type == OP and token_val == ')':
                            in_arguments = False
                            print("ARGUMENTS END ->>>>")
                            result.append((token_type, token_val))
                        ##########
                        # ARGUMENT ( we add type if we have one )
                        ##########
                            # todo - detect if default value
                        elif in_arguments and not type_detected and token_type == NAME:
                            print(f"ARGUMENT ----> {token_val}")
                            updated_arg_tokens = [(token_type, token_val)]
                            # check if we have a type for the argument
                            # dont worry about pre existing types, we drop them somewhere else
                            types_detected_for_agument = data[mfl]["args"]
                            if token_val in types_detected_for_agument:
                                arg_types = types_detected_for_agument[token_val]
                                # skip method self or class method ref
                                if arg_types[0] == SELF_OR_CLS:
                                    pass
                                # if just one arg, get it out of the array
                                elif len(arg_types) == 1:
                                    colon_token = (OP, ':')
                                    type_token = (STRING, arg_types[0])
                                    updated_arg_tokens.append(colon_token)
                                    updated_arg_tokens.append(type_token)
                                # otherwise, stringify entire array and add as is
                                else:
                                    colon_token = (OP, ':')
                                    type_token = (STRING, str(arg_types))
                                    updated_arg_tokens.append(colon_token)
                                    updated_arg_tokens.append(type_token)
                            result.extend(updated_arg_tokens)
                        # in argument, we detected a colon (:) which means we have a type
                        elif in_arguments and token_type == OP and token_val == ':':
                            print(f"TYPE DETECTED ")
                            type_detected = True
                            # result.append((token_type, token_val))
                        elif in_arguments and type_detected and token_type == NAME:
                            print(f"DROPPING OLD TYPE")
                            type_detected = False
                        # handle indentation
                        elif token_type == INDENT:
                            print(f"INDENTATION detected")
                            result.append((token_type, token_val))
                            indentation.append(token_val)
                        else:
                            print('OTHER tokens')
                            result.append((token_type, token_val))
                    updated_function = untokenize(result)
                    updated_function_with_indentation = ''.join(indentation) + updated_function
                    print(">"*10)
                    print("OLD")
                    print(line)
                    print(">"*10)
                    print("NEW")
                    print(updated_function_with_indentation)
                    updated_function_declarations[mfl] = updated_function_with_indentation
                    print("DATA ->>>>")
                    print(data)
    return updated_function_declarations

if __name__ == "__main__":
    print("===== STAGE 1 - RECORD DATA =====")
    f = Foo()
    with trace() as data:
        print("-" * 20, " RESULT: ", "-" * 20)
        # example_function_with_third_party_lib(1,2)
        f.arbitrary_self(
            1,
            2,
        )
        f.arbitrary_self(
            1,
            2,
        )
        f.arbitrary_self(
            '1',
            '2',
        )
    pprint.pprint(data, sort_dicts=False)

    print("===== STAGE 2 - ANALYSE TYPES IN DATA =====")
    print(f"DATA AFTER 1st STAGE ----> {data}")
    types_data = convert_results_to_types(data)
    pprint.pprint(types_data, sort_dicts=False)

    print("===== STAGE 3 - UPDATE FILE WITH TYPES =====")
    update_code_with_types(types_data)
