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
from typemedaddy.foo import example_function_with_third_party_lib, Foo, takes_func_returns_func, int_function, example_function
from types import FrameType, FunctionType
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


def is_class(obj):
    # we filter non-user calls upstream, so we should only get user defined classes at this stage
    if obj is None:
        return False
    return isinstance(obj, object) and not isinstance(
        obj, (int, float, str, list, dict, tuple, set, FunctionType)
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
                # SPECIAL CASE - CLASS
                if is_class(var):
                    var = f"USER_CLASS|{var.__module__}::{var_type}"
            if arg_name in RESULT[mod_func_line]["args"]:
                RESULT[mod_func_line]["args"][arg_name].append(var)
            else:
                RESULT[mod_func_line]["args"][arg_name] = [var]
    ##################
    ##### RETURN #####
    ##################
    elif event == TraceEvent.RETURN:
        if is_class(arg):
            arg = f"USER_CLASS|{arg.__module__}::{type(arg).__name__}"
        if "return" in RESULT[mod_func_line]:
            RESULT[mod_func_line]["return"].append(arg)
        else:
            RESULT[mod_func_line]["return"] = [arg]
    return trace_function


def sort_types_none_at_the_end(set_of_types: set[str]|list[str]) -> list:
    is_none = False
    temp = set()
    for x in list(set_of_types)[:]:
        if "None" in x:
            if x == "None":
                is_none = True
            else:
                temp.add(x)
            set_of_types.remove(x)
    sorted_types: list = sorted(set_of_types)
    for y in temp:
        sorted_types.append(y)
    if is_none:
        sorted_types.append('None')
    return sorted_types

def get_value_type(val: Any) -> str:
    # type(None) -> NoneType, which we don't really want, because type hint 
    # system uses None string, not NoneType
    if val == None:
        return  'None'
    else:
        return type(val).__name__

def union_types(types: list[str|tuple[str,str]]) -> str:
    if not sys.version_info.minor > 9:
        raise Exception('This union is supported only by python 3.10+')
    # we use dict to 'merge' same types into same buckets
    temp_dict = {}
    for x in types:
        # if simple, shallow type
        if type(x) == str:
            temp_dict[x] = x
        # if tuple - ie, complex or nested type complex / simple type
        else:
            outer, inner = x
            if outer in temp_dict:
                if outer == 'simple':
                    temp_dict[inner].add(inner)
                elif outer == 'self':
                    temp_dict[SELF_OR_CLS].add()#todo - test this 
                else:
                    temp_dict[outer].add(inner)
            else:
                if outer == 'simple':
                    temp_dict[inner] = {inner}
                elif outer == 'self':
                    temp_dict[SELF_OR_CLS] = {} #todo - test this 
                else:
                    temp_dict[outer] = {inner}
    result = set()
    for k,v in temp_dict.items():
        if k not in COLLECTIONS:
            result.add(k)
        else:
            # rembmer to sort the set!
            sorted_joined_types = '|'.join(sorted(v))
            if sorted_joined_types:
                result.add(f"{k}[{sorted_joined_types}]")
            else:
                result.add(k)
    return '|'.join(sort_types_none_at_the_end(result))

def union_dict_types(types: dict[str,set[tuple[str,str]]]) -> str:
    if not sys.version_info.minor > 9:
        raise Exception('This union is supported only by python 3.10+')
    temp_set = set()
    for k,v in types.items():
        sorted_types = sort_types_none_at_the_end(v)
        union_of_sorted_types = f"{k},{union_types(sorted_types)}"
        temp_set.add(union_of_sorted_types)
    sorted_set = sorted(temp_set)
    return union_types(sorted_set)

def convert_value_to_type(value: Any) -> tuple[Literal["dict", "tuple", "list", "set", "self", "simple"], str]:
    input_type = get_value_type(value)
    # base case
    if input_type not in COLLECTIONS:
        # hardcoded - special case - self reference arg in methods
        if value == SELF_OR_CLS:
            return ('self', value)
        else:
            if input_type == 'function':
                return ('simple', 'Callable')
            return ('simple', input_type)
    if input_type == "dict":
        temp_dict = {}
        for k, v in value.items():
            key_type = get_value_type(k)
            if key_type in temp_dict:
                temp_dict[key_type].add(convert_value_to_type(v))
            else:
                temp_dict[key_type] = {convert_value_to_type(v)}
        if temp_dict:
            union_of_sorted_types = union_dict_types(temp_dict)
            input_type = (input_type, union_of_sorted_types)
        else:
            input_type = (input_type, '')
    elif input_type in COLLECTIONS_NO_DICT:
        types_found_in_collection = set()
        for v in value:
            types_found_in_collection.add(convert_value_to_type(v))
        if types_found_in_collection:
            sorted_types = sort_types_none_at_the_end(types_found_in_collection)
            union_of_sorted_types = union_types(sorted_types)
            input_type = (input_type, union_of_sorted_types)
        else:
            input_type = (input_type, '')
    else:
        raise Exception(f'Unexpected type : {input_type}')
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
        # ==========================
        # ========== ARGS ==========
        # ==========================
        result[mfl] = {"args": dict()}  # init result
        for arg in input[mfl]["args"]:
            # lets use set to de-dup types
            s = set()
            result[mfl]["args"][arg] = list()  # init result
            # iterate over function's every arguemnt, and it's values
            for value in input[mfl]["args"][arg]:
                value_type = union_types([convert_value_to_type(value)])
                s.add(value_type)
            # we sort the output, to get deterministic results -> set has random ordering
            # TODO this returns array of types, which we will have to collapse again?
            result[mfl]["args"][arg] = sorted(s)
        # ============================
        # ========== RETURN ==========
        # ============================
        result[mfl]["return"] = list()
        # lets use set to de-dup types
        s = set()
        for value in input[mfl]["return"]:
            value_type = union_types([convert_value_to_type(value)])
            s.add(value_type)
            # we sort the output, to get deterministic results -> set has random ordering
        result[mfl]["return"] = sorted(s)
    return result

def update_code_with_types(data: dict) -> dict[str, object]:
    updated_function_declarations = dict()
    for mfl in data:
        new_module = []
        if mfl.count(":") > 2:
            raise Exception("Detected too many separators! Perhaps function name contains a colon?")
        module, function, line_num = mfl.split(":")
        with open(module, "r") as f:
            for idx, line in enumerate(f):
                # find a line containting the function
                if idx == int(line_num) - 1: # todo - test multiline function declaration
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
                                arg_type = types_detected_for_agument[token_val]
                                assert type(arg_type) == str
                                # skip method self or class method ref
                                if arg_type == SELF_OR_CLS:
                                    pass
                                else:
                                    colon_token = (OP, ':')
                                    type_token = (STRING, arg_type)
                                    updated_arg_tokens.append(colon_token)
                                    updated_arg_tokens.append(type_token)
                            result.extend(updated_arg_tokens)
                        # in argument, we detected a colon (:) which means we have a type
                        elif in_arguments and token_type == OP and token_val == ':':
                            print(f"TYPE DETECTED, DROPPING COLON")
                            type_detected = True
                        elif in_arguments and type_detected and token_type == NAME:
                            print(f"DROPPING OLD TYPE")
                        elif in_arguments and type_detected and token_type == OP and token_val == '|':
                            print(f"DROPPING PIPE")
                        elif in_arguments and type_detected and token_type == OP and token_val == ',':
                            print(f"END of types for argument")
                            type_detected = False
                            result.append((token_type, token_val))
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

def detect_multiple_arg_types(stage_2_results: dict) -> str:
    warnings = []
    for mfl, type_info in stage_2_results.items():
        for arg, arg_types in type_info['args'].items():
            if len(arg_types) > 1:
                warnings.append(f"{mfl} - argument: {arg} - has {len(arg_types)} types: {arg_types}")
        return_types = type_info['return']
        if len(return_types) > 1:
            warnings.append(f"{mfl} - return argument has {len(return_types)} types: {return_types}")
    return '\n'.join(warnings)

def unify_types_in_final_result(stage_2_results: dict) -> dict:
    for _, type_info in stage_2_results.items():
        for arg, arg_types in type_info['args'].items():
            assert type(arg_types) == list
            sorted_args = sort_types_none_at_the_end(arg_types)
            type_info['args'][arg] = '|'.join(sorted_args)
        return_types = type_info['return']
        assert type(return_types) == list
        sorted_return = sort_types_none_at_the_end(return_types)
        type_info['return'] = '|'.join(sorted_return)
    return stage_2_results

if __name__ == "__main__":
    print("===== STAGE 1 - RECORD DATA =====")
    f = Foo()
    with trace() as data:
        print("-" * 20, " RESULT: ", "-" * 20)
        # example_function_with_third_party_lib(1,2)
        # f.arbitrary_self(
        #     1,
        # )
        # f.arbitrary_self(
        #     1,
        #     2,
        # )
        # f.arbitrary_self(
        #     '1',
        #     '2',
        # )
        # takes_func_returns_func(int_function)
        f = Foo()
        example_function(1, 2, f)
        example_function(3, 4, None)
        example_function('a', 'b', None)
    pprint.pprint(data, sort_dicts=False)

    print("===== STAGE 2 - ANALYSE TYPES IN DATA =====")
    print(f"DATA AFTER 1st STAGE ----> {data}")
    types_data = convert_results_to_types(data)
    print("===== STAGE 4 - DETECT MULIPLE ARG TYPS =====")
    warnings = detect_multiple_arg_types(types_data)
    if warnings:
        print(warnings)
    pprint.pprint(types_data, sort_dicts=False)
    print("===== STAGE 5 - UNIFY ALL TYPES =====")
    unified_types_data = unify_types_in_final_result(types_data)
    print("===== STAGE 6 - UPDATE FILE WITH TYPES =====")
    update_code_with_types(types_data)
