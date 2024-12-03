import inspect
from typing import Union
import ast
from collections import namedtuple
import io
import shutil
from tokenize import INDENT, untokenize, STRING, NAME, OP, generate_tokens
import logging
import contextlib
from typing import Any
import sys
import os
from enum import Enum
import argparse
from types import FrameType, FunctionType
from typing import Literal
from autopep8 import fix_code

# take logger args, if we are running directly
# ( this bit was executing when running tests, so I put it in a conditional)
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default="INFO")
    args = parser.parse_args()
    log_level = args.log.upper()
    if log_level in ("DEBUG", "INFO", "WARNING", "ERROR"):
        logging.basicConfig(level=log_level)
    else:
        logging.basicConfig(level="INFO")
LOG = logging.getLogger(__name__)

# constants
if not sys.version_info.minor > 5:
    raise Exception("Python 3.5+ is a minimum required to run this show")
if sys.version_info.minor >= 5 and sys.version_info.minor <= 9:
    UNION_OPERATOR = lambda x: f"Union[{', '.join(x)}]" if len(x) > 1 else x[0]
else:
    UNION_OPERATOR = lambda x: "|".join(x)
COLLECTIONS = ("dict", "list", "set", "tuple")
COLLECTIONS_NO_DICT = ("list", "set", "tuple")
SELF_OR_CLS = "SELF_OR_CLS"
RESULT = {}
IMPORTS = set()
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
TREES = {}

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
    elif "__module__" not in dir(obj):  # we skip cell objects
        return False
    return isinstance(obj, object) and not isinstance(
        obj, (int, float, str, list, dict, tuple, set, FunctionType)
    )


# we use context for easy testing, same with the RESULT yields, for tests only
@contextlib.contextmanager
def trace():
    global RESULT
    LOG.info("========== TRACING ON ==========\n\n")
    sys.settrace(trace_function)
    try:
        yield RESULT
    finally:
        LOG.info("========== TRACING OFF ==========\n\n")
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
    if "venv" in module_name or PROJECT_NAME not in module_name or func_name in ("trace", "<genexpr>", "<lambda>", "<module>"):
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
        # check if current frame is executing a class code -> I don't really understand in what situation this can happen, but it does
        frame_info = inspect.getframeinfo(frame)
        if frame_info and frame_info.code_context:
            code_context = frame_info.code_context[0]
            first_chunk_of_executed_code = code_context.split(' ')[0]
            if first_chunk_of_executed_code == 'class':
                LOG.debug(f'Code context is executing a class: {mod_func_line}. Skipping')
                return trace_function
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
                LOG.debug("--- end ---")
                # SPECIAL CASE - CLASS
                if is_class(var):
                    # update imports global so that we can update the files in the final stage
                    IMPORTS.add((mod_func_line, var.__module__, var_type))
                    var = f"USER_CLASS|{var.__module__}::{var_type}"
            if arg_name in RESULT[mod_func_line]["args"]:
                RESULT[mod_func_line]["args"][arg_name].append(var)
            else:
                RESULT[mod_func_line]["args"][arg_name] = [var]
    ##################
    ##### RETURN #####
    ##################
    elif event == TraceEvent.RETURN:
        if mod_func_line not in RESULT:
            LOG.debug(f"Return from a function that wasn't invoked yet! Skipping it: {mod_func_line}")
        if is_class(arg):
            arg = f"USER_CLASS|{arg.__module__}::{type(arg).__name__}"
        if "return" in RESULT[mod_func_line]:
            RESULT[mod_func_line]["return"].append(arg)
        else:
            RESULT[mod_func_line]["return"] = [arg]
    return trace_function


def sort_types_none_at_the_end(set_of_types: Union[set[str], list[str]]) -> list:
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
        sorted_types.append("None")
    return sorted_types


def get_value_type(val: Any) -> str:
    # type(None) -> NoneType, which we don't really want, because type hint
    # system uses None string, not NoneType
    if val is None:
        return "None"
    else:
        return type(val).__name__


def union_types(types: list[Union[str, tuple[str, str]]]) -> str:
    # we use dict to 'merge' same types into same buckets
    temp_dict: dict[str, Union[str, set[str]]] = {}
    for x in types:
        # if simple, shallow type
        if type(x) is str:
            temp_dict[x] = x
        # if tuple - ie, complex or nested type complex / simple type
        else:
            outer, inner = x
            assert outer in ("dict", "tuple", "list", "set", "self", "simple", "class")
            if outer in temp_dict:
                if outer in ("simple", "class"):
                    temp_dict[inner] = inner
                elif outer == "self":
                    temp_dict[SELF_OR_CLS] = SELF_OR_CLS
                else:
                    temp_dict[outer].add(inner)
            else:
                if outer == "simple" or outer == "class":
                    temp_dict[inner] = {inner}
                elif outer == "self":
                    temp_dict[SELF_OR_CLS] = set()
                else:
                    temp_dict[outer] = {inner}
    result = set()
    for k, v in temp_dict.items():
        if k not in COLLECTIONS:
            result.add(k)
        else:
            # rembmer to sort the set!
            sorted_joined_types = UNION_OPERATOR(sorted(v))
            if sorted_joined_types:
                result.add(f"{k}[{sorted_joined_types}]")
            else:
                result.add(k)
    return UNION_OPERATOR(sort_types_none_at_the_end(result))


def union_dict_types(types: dict[str, set[tuple[str, str]]]) -> str:
    temp_set = set()
    for k, v in types.items():
        sorted_types = sort_types_none_at_the_end(v)
        union_of_sorted_types = f"{k},{union_types(sorted_types)}"
        temp_set.add(union_of_sorted_types)
    sorted_set = sorted(temp_set)
    return union_types(sorted_set)


def convert_value_to_type(
    value: Any,
) -> tuple[Literal["dict", "tuple", "list", "set", "self", "simple", "class"], str]:
    input_type = get_value_type(value)
    # base case
    if input_type not in COLLECTIONS:
        # hardcoded - special case - self reference arg in methods
        if type(value) is str:
            if value == SELF_OR_CLS:
                return ("self", value)
            elif "USER_CLASS" in value:
                class_name = value.split("::")[1]
                return ("class", class_name)
        else:
            if input_type == "function":
                return ("simple", "Callable")
        return ("simple", input_type)
    if input_type == "dict":
        temp_dict = {}
        for k, v in value.items():
            key_type = get_value_type(k)
            temp_dict.setdefault(key_type, set()).add(convert_value_to_type(v))
        if temp_dict:
            union_of_sorted_types = union_dict_types(temp_dict)
            input_type = (input_type, union_of_sorted_types)
        else:
            input_type = (input_type, "")
    elif input_type in COLLECTIONS_NO_DICT:
        types_found_in_collection = set()
        for v in value:
            types_found_in_collection.add(convert_value_to_type(v))
        if types_found_in_collection:
            sorted_types = sort_types_none_at_the_end(types_found_in_collection)
            union_of_sorted_types = union_types(sorted_types)
            input_type = (input_type, union_of_sorted_types)
        else:
            input_type = (input_type, "")
    else:
        raise Exception(f"Unexpected type : {input_type}")
    return input_type


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
        _, f, _ = mfl.split(":")
        if f == "<module>" or f == "<lambda>":
            continue
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

def get_size_of_function_sig(module: str, code: str, f_name: str):
    if module in TREES:
        tree = TREES[module]
    else:
        tree = ast.parse(code)
        TREES[module] = tree
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == f_name:
            start = int(node.lineno) - 1
            try:
                end = int(node.args.args[-1].lineno) # get the line of the last argument
            except IndexError:
                end = start # no args scenario
            return (start, end)
    raise Exception(f"Failed to find the function in the ast tree. Function name: {f_name}")

def get_tokens(code: str, s: int, e: int):
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
    if s == -1:
        raise Exception('Invalid input')
    lines_to_tokenize = "\n".join(code.splitlines()[s:e])
    lines = io.StringIO(lines_to_tokenize).readline
    tokens = generate_tokens(lines)
    return tokens

def execute_update(mfl: str, data: dict, updated_function_declarations: dict) -> None:
    if mfl.count(":") > 2:
        raise Exception("Detected too many separators! Perhaps function name contains a colon?")
    module, function, line_num = mfl.split(":")
    with open(module, "r") as f:
        code = f.read()
        f_start, f_end = get_size_of_function_sig(module, code, function)
        tokens = get_tokens(code, f_start, f_end)
        result = []
        in_arguments = None
        # untokenize will not handle spacing and indentation if we remove last 3 args
        # so we have to handle it manually
        indentation = []
        type_detected = False
        for t in tokens:
            # we care only about first 2 values, type is a number mapped in an ENUM
            token_type, token_val, _, _, _ = t
            # start of arguments
            if token_type == OP and token_val == "(":
                """ARGUMENTS START"""
                in_arguments = True
                result.append(
                    (
                        token_type,
                        token_val,
                    )
                )
            # end of arguments
            elif token_type == OP and token_val == ")":
                """ARGUMENTS END"""
                in_arguments = False
                result.append((token_type, token_val))
            ##########
            # ARGUMENT ( we add type if we have one )
            ##########
            elif in_arguments and not type_detected and token_type == NAME:
                updated_arg_tokens = [(token_type, token_val)]
                # check if we have a type for the argument
                # dont worry about pre existing types, we drop them somewhere else
                types_detected_for_agument = data[mfl]["args"]
                if token_val in types_detected_for_agument:
                    arg_type = types_detected_for_agument[token_val]
                    assert type(arg_type) is str
                    # skip method self or class method ref
                    if arg_type == SELF_OR_CLS:
                        pass
                    else:
                        colon_token = (OP, ":")
                        type_token = (STRING, arg_type)
                        updated_arg_tokens.append(colon_token)
                        updated_arg_tokens.append(type_token)
                result.extend(updated_arg_tokens)
            # in argument, we detected a colon (:) which means we have a type
            elif in_arguments and token_type == OP and token_val == ":":
                """TYPE DETECTED, DROPPING COLON"""
                type_detected = True
                # edge case - None is of type NAME, we do not handle default values
                # if def value is set to None, it fall through here
                # NO, I will not refactor this mess, it works!
            elif (
                in_arguments
                and type_detected
                and token_type == NAME
                and token_val != "None"
            ):
                """DROPPING OLD TYPE"""
            elif (
                in_arguments and type_detected and token_type == OP and token_val == "|"
            ):
                """DROPPING PIPE"""
            elif (
                in_arguments and type_detected and token_type == OP and token_val == ","
            ):
                type_detected = False
                result.append((token_type, token_val))
            # RETURN VALUE
            elif (
                in_arguments is False
            ):  # specifically False, not None, this means we just finished arguments and start return
                if token_type == OP:
                    if token_val == ":":
                        # this is a start, so no pre - existing type
                        # check if we have a return type for this function
                        if data[mfl]["return"]:
                            tokens = []
                            tokens.append((OP, "->"))
                            tokens.append((NAME, data[mfl]["return"]))
                            tokens.append((OP, ":"))
                            result.extend(tokens)
                            break  # we are done, bail
                        else:
                            result.append((OP, ":"))  # no type found, add : and bail
                            break
            # handle indentation
            elif token_type == INDENT:
                """INDENTATION detected"""
                result.append((token_type, token_val))
                indentation.append(token_val)
            else:
                """OTHER tokens"""
                result.append((token_type, token_val))
        updated_function = untokenize(result)
        # we keep indentation separate for now next step will reformat code, and we don't want it to remove whitespace
        updated_function_declarations[mfl] = ("".join(indentation), updated_function)

def update_code_with_types(data: dict) -> dict[str, tuple[str, str]]:
    updated_function_declarations = dict()
    for mfl in data:
        try:
            execute_update(mfl, data, updated_function_declarations)
        except Exception:
            LOG.error(f"Function signature update failed -> {mfl}")
            if mfl in RESULT:
                del RESULT[mfl]
                LOG.warn(f"Deleted {mfl} from RESULT after failed code update")
            # raise
    return updated_function_declarations


def detect_multiple_arg_types(stage_2_results: dict) -> str:
    warnings = []
    for mfl, type_info in stage_2_results.items():
        for arg, arg_types in type_info["args"].items():
            if len(arg_types) > 1:
                warnings.append(
                    f"{mfl} - argument: {arg} - has {len(arg_types)} types: {arg_types}"
                )
        return_types = type_info["return"]
        if len(return_types) > 1:
            warnings.append(
                f"{mfl} - return argument has {len(return_types)} types: {return_types}"
            )
    return "\n".join(warnings)


def unify_types_in_final_result(stage_2_results: dict) -> dict:
    for _, type_info in stage_2_results.items():
        for arg, arg_types in type_info["args"].items():
            assert type(arg_types) is list
            sorted_args = sort_types_none_at_the_end(arg_types)
            type_info["args"][arg] = UNION_OPERATOR(sorted_args)
        return_types = type_info["return"]
        assert type(return_types) is list
        sorted_return = sort_types_none_at_the_end(return_types)
        type_info["return"] = UNION_OPERATOR(sorted_return)
    return stage_2_results


def reformat_code(function_signatures: dict[str, tuple[str, str]]) -> dict[str, object]:
    result = {}
    for mfl, v in function_signatures.items():
        indentation, code = v
        result[mfl] = indentation + fix_code(code)
    return result


def get_modules_with_union_types(
    function_signatures: dict[str, tuple[str, str]],
) -> set[tuple[str, str, str]]:
    result: set[tuple[str, str, str]] = set()
    for mfl, v in function_signatures.items():
        _, code = v
        if "Union[" in code:
            result.add((mfl, "typing", "Union"))
    return result


FLC = namedtuple("FLC", ["function_name", "line", "function_signature"])


def update_files_with_new_signatures(
    function_signatures: dict[str, object], backup_file_suffix: Union[str, None] = "bak"
) -> dict[str, FLC]:
    # {module = [('func_name', 'line', '<CODE>')] [str,str,str]
    modules = {}
    # group by module so we update file only once
    for mfl, f_signature in function_signatures.items():
        module, function, line = mfl.split(":")
        modules.setdefault(module, list()).append((function, line, f_signature))
    for module in modules:
        # read lines
        with open(module, "r") as f:
            lines = f.readlines()
        # create backup
        if backup_file_suffix:
            shutil.copy(module, f"{module}.{backup_file_suffix}")
            LOG.info(f"created backup at location: {module}.{backup_file_suffix}")
        for function, line, f_signature in modules[module]:
            # update ( 0 indexed )
            lines[int(line) - 1] = str(f_signature)
        # write lines
        with open(module, "w") as f:
            f.writelines(lines)
    return modules


def update_files_with_new_imports(
    imports: set[tuple[str, str, str]], backup_file_suffix="bak"
) -> None:
    # group by files, just like in code update stage, but this time we just need module and class name
    modules = {}
    for mfl, module, class_name in imports:
        file_path, _, _ = mfl.split(":")
        modules.setdefault(file_path, set()).add((module, class_name))
    for file_path in modules:
        # read lines
        missing_imports = set()
        with open(file_path, "r") as f:
            tree = ast.parse(f.read(), filename=file_path)
            # get import nodes
            imported_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        imported_names.add(alias.name)
            # check if class name exists in imported names
            for module, class_name in modules[file_path]:
                if class_name not in imported_names:
                    missing_imports.add((module, class_name))
            if not missing_imports:
                continue
        # if we have mising imports, read all the lines
        with open(file_path, "r") as f:
            original_file = f.readlines()
        # generate new import lines
        new_imports = [
            f"from {module} import {class_name}\n" for module, class_name in missing_imports
        ]
        file_with_new_imports = new_imports + original_file
        # # create backup
        if backup_file_suffix:
            if os.path.isfile(f"{file_path}.{backup_file_suffix}"):
                print(
                    f"Backup file at location: {file_path}.{backup_file_suffix} already exits, skipping"
                )
            else:
                shutil.copy(file_path, f"{file_path}.{backup_file_suffix}")
                print(f"Created backup at location: {file_path}.{backup_file_suffix}")
        # write new file
        with open(file_path, "w") as f:
            f.writelines(file_with_new_imports)


def print_warnings(warnings: str) -> None:
    if warnings:
        LOG.warning("=" * 50)
        LOG.warning("====================" + " WARNINGS " + "====================")
        LOG.warning("=" * 50 + "\n\n")
        LOG.warning(warnings + "\n\n")
        LOG.warning("=" * 50)
        LOG.warning("=" * 50)


def type_it_like_its_hot(data: dict) -> None:
    LOG.info("Converting results to types")
    types_data = convert_results_to_types(data)
    warnings = detect_multiple_arg_types(types_data)
    unified_types_data = unify_types_in_final_result(types_data)
    updated_function_signatures = update_code_with_types(unified_types_data)
    reformatted_function_signatures = reformat_code(updated_function_signatures)
    LOG.info("Updating files with new signatures")
    update_files_with_new_signatures(reformatted_function_signatures)
    LOG.info("Adding imports fro classes")
    update_files_with_new_imports(IMPORTS)
    if sys.version_info.minor >= 5 and sys.version_info.minor <= 9:
        modules_with_unions = get_modules_with_union_types(updated_function_signatures)
        LOG.info("Adding imports for Union types")
        update_files_with_new_imports(modules_with_unions)
    LOG.info("Finished\n\n")
    print_warnings(warnings)
