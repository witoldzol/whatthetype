import shutil
import filecmp
from pathlib import Path
import pytest
from typemedaddy.foo import (
    example_function,
    Foo,
    function_returning_dict,
    int_function,
    returns_a_class,
    func_that_takes_any_args,
    takes_func_returns_func,
)
from typemedaddy.typemedaddy import (
    convert_results_to_types,
    convert_value_to_type,
    trace,
    SELF_OR_CLS,
    update_code_with_types,
    unify_types_in_final_result,
    union_types,
    reformat_code,
    update_files_with_new_signatures
)

MODULE_PATH = "typemedaddy.foo"


def test_example_function():
    with trace() as actual:
        f = Foo()  # this will trigger def __init__ which will get captured
        example_function(1, 2, f)
    for k in actual:
        print(k)
        if "init" in k:
            assert actual[k]["args"] == {"self": [SELF_OR_CLS], "bar": [None]}
            assert actual[k]["return"] == [None]
        elif "example_function" in k:
            assert actual[k]["args"] == {
                "a": [1],
                "b": [2],
                "foo": [f"USER_CLASS|{MODULE_PATH}::Foo"],
            }
            assert actual[k]["return"] == [3]


def test_if_global_context_is_not_polluted_by_previous_test_invocation():
    with trace() as actual:
        f = Foo()
        example_function(1, 2, f)
        example_function(3, 4, None)
    for k in actual:
        if "init" in k:
            assert actual[k]["args"] == {"self": [SELF_OR_CLS], "bar": [None]}
            assert actual[k]["return"] == [None]
        elif "example_function" in k:
            assert actual[k]["args"] == {
                "a": [1, 3],
                "b": [2, 4],
                "foo": [f"USER_CLASS|{MODULE_PATH}::Foo", None],
            }
            assert actual[k]["return"] == [3, 7]


def test_example_function_with_different_args():
    with trace() as actual:
        f = Foo()
        example_function(1, 2, f)
        example_function("bob", "wow", f)
    for k in actual:
        if "init" in k:
            assert actual[k]["args"] == {"self": [SELF_OR_CLS], "bar": [None]}
            assert actual[k]["return"] == [None]
        elif "example_function" in k:
            assert actual[k]["args"] == {
                "a": [1, "bob"],
                "b": [2, "wow"],
                "foo": [f"USER_CLASS|{MODULE_PATH}::Foo", f"USER_CLASS|{MODULE_PATH}::Foo"],
            }
            assert actual[k]["return"] == [3, "bobwow"]


def test_class_method():
    f = Foo()
    with trace() as actual:
        f.get_foo("bob", 9)
    for k in actual:
        assert actual[k]["args"] == {
            "self": [SELF_OR_CLS], "name": ["bob"], "age": [9]}
        assert actual[k]["return"] == ["bob,9"]


def test_method_returns_a_class():
    with trace() as actual:
        returns_a_class()
    for k in actual:
        if "init" in k:
            assert actual[k]["args"] == {"self": [SELF_OR_CLS], "bar": [None]}
            assert actual[k]["return"] == [None]
        elif "returns_a_class" in k:
            assert actual[k]["args"] == {}
            assert actual[k]["return"] == [f"USER_CLASS|{MODULE_PATH}::Foo"]


def test_function_returning_dict():
    with trace() as actual:
        function_returning_dict()
    for k in actual:
        assert actual[k]["args"] == {}
        assert actual[k]["return"] == [
            {
                "foo": {
                    "bar": 2,
                },
                "value": 1,
            }
        ]


def test_int_function():
    with trace() as actual:
        int_function(1)
    for k in actual:
        assert actual[k]["args"] == {"i": [1]}
        assert actual[k]["return"] == [1]


# ====== STAGE 2 TESTS -> CONVERT RESULT TO TYPES ======


def test_empty_result():
    r = convert_results_to_types({})
    assert r == {}


MODEL = {
    "module:func_name:func_line": {
        "args": {"var_name": set("type")},
        "return": set("type"),
    }
}


def test_one_function():
    step_1_result = {
        "/home/w/repos/typemedaddy/foo.py:int_function:18": {
            "args": {"a": [1], "b": [2.0], "c": [3], "d": ["4"]},
            "return": [1],
        }
    }
    actual = convert_results_to_types(step_1_result)
    expected = {
        "/home/w/repos/typemedaddy/foo.py:int_function:18": {
            "args": {"a": ["int"], "b": ["float"], "c": ["int"], "d": ["str"]},
            "return": ["int"],
        }
    }
    assert actual == expected


def test_multiple_functions():
    step_1_result = {
        "/home/w/repos/typemedaddy/foo.py:int_function:18": {
            "args": {"a": [1], "b": [2], "c": [3], "d": ["4"]},
            "return": [1],
        },
        "/home/w/repos/typemedaddy/bar.py:bar_function:69": {
            "args": {"a": [1]},
            "return": [1],
        },
    }
    actual = convert_results_to_types(step_1_result)
    expected = {
        "/home/w/repos/typemedaddy/foo.py:int_function:18": {
            "args": {"a": ["int"], "b": ["int"], "c": ["int"], "d": ["str"]},
            "return": ["int"],
        },
        "/home/w/repos/typemedaddy/bar.py:bar_function:69": {
            "args": {"a": ["int"]},
            "return": ["int"],
        },
    }
    assert actual == expected


def test_multiple_type_inputs_for_the_same_param():
    step_1_result = {
        "/home/w/repos/typemedaddy/foo.py:int_function:18": {
            "args": {"a": [1, "1"]},
            "return": [1, "1"],
        },
        "/home/w/repos/typemedaddy/bar.py:bar_function:69": {
            "args": {"a": [1, "1"]},
            "return": [1, "1"],
        },
    }
    actual = convert_results_to_types(step_1_result)
    # expected = {
    #     "/home/w/repos/typemedaddy/foo.py:int_function:18": {
    #         "args": {"a": ["int", "str"]},
    #         "return": ["int", "str"],
    #     },
    #     "/home/w/repos/typemedaddy/bar.py:bar_function:69": {
    #         "args": {"a": ["int", "str"]},
    #         "return": ["int", "str"],
    #     },
    # }
    assert sorted(actual["/home/w/repos/typemedaddy/foo.py:int_function:18"]
                  ["args"]["a"]) == sorted(["str", "int"])
    assert sorted(actual["/home/w/repos/typemedaddy/foo.py:int_function:18"]
                  ["return"]) == sorted(["str", "int"])
    assert sorted(actual["/home/w/repos/typemedaddy/bar.py:bar_function:69"]
                  ["args"]["a"]) == sorted(["str", "int"])
    assert sorted(actual["/home/w/repos/typemedaddy/bar.py:bar_function:69"]
                  ["return"]) == sorted(["str", "int"])


def test_conver_self_ref_val_to_self_ref_type():
    step_1_result = {
        '/home/w/repos/typemedaddy/typemedaddy/foo.py:arbitrary_self:12': {
            'args': {'not_self': ['SELF_OR_CLS'],
                     'name': [1],
                     'age': [2]},
            'return': ['1,2']
        },
    }
    actual = convert_results_to_types(step_1_result)
    expected = {
        "/home/w/repos/typemedaddy/typemedaddy/foo.py:arbitrary_self:12": {
            'args': {'not_self': ['SELF_OR_CLS'],
                     'name': ['int'],
                     'age': ['int']},
            'return': ['str']
        }
    }
    assert actual == expected


def test_empty_list():
    step_1_result = {
        "/home/w/repos/typemedaddy/foo.py:int_function:18": {
            "args": {"a": [[]]},
            "return": [[]],
        }
    }
    actual = convert_results_to_types(step_1_result)
    expected = {
        "/home/w/repos/typemedaddy/foo.py:int_function:18": {
            "args": {"a": ["list"]},
            "return": ["list"],
        }
    }
    assert actual == expected


def test_int_list():
    step_1_result = {
        "/home/w/repos/typemedaddy/foo.py:int_function:18": {
            "args": {"a": [[1]], "b": [[1, 2]]},
            "return": [[1]],
        }
    }
    actual = convert_results_to_types(step_1_result)
    expected = {
        "/home/w/repos/typemedaddy/foo.py:int_function:18": {
            "args": {"a": ["list[int]"], "b": ["list[int]"]},
            "return": ["list[int]"],
        }
    }
    assert actual == expected


def test_nested_empty_list():
    step_1_result = {
        "/home/w/repos/typemedaddy/foo.py:int_function:18": {
            "args": {"a": [[[]]]},
            "return": [[[]]],
        }
    }
    actual = convert_results_to_types(step_1_result)
    expected = {
        "/home/w/repos/typemedaddy/foo.py:int_function:18": {
            "args": {"a": ["list[list]"]},
            "return": ["list[list]"],
        }
    }
    assert actual == expected


def test_nested_int_list():
    step_1_result = {
        "/home/w/repos/typemedaddy/foo.py:int_function:18": {
            "args": {"a": [[[1]]]},
            "return": [[[1]]],
        }
    }
    actual = convert_results_to_types(step_1_result)
    expected = {
        "/home/w/repos/typemedaddy/foo.py:int_function:18": {
            "args": {"a": ["list[list[int]]"]},
            "return": ["list[list[int]]"],
        }
    }
    assert actual == expected


def test_convert_value_to_type():
    value = 1
    actual = convert_value_to_type(value)
    assert ("simple", "int") == actual

    value = 'a'
    actual = convert_value_to_type(value)
    assert ("simple", "str") == actual

    value = 1.0
    actual = convert_value_to_type(value)
    assert ("simple", "float") == actual

    value = None
    actual = convert_value_to_type(value)
    assert ("simple", "None") == actual

    # list
    value = []
    actual = convert_value_to_type(value)
    assert ("list", '') == actual

    value = [1]
    actual = convert_value_to_type(value)
    assert ("list", "int") == actual

    value = [1.0]
    actual = convert_value_to_type(value)
    assert ("list", "float") == actual

    value = ['a']
    actual = convert_value_to_type(value)
    assert ("list", "str") == actual

    value = [None]
    actual = convert_value_to_type(value)
    assert ('list', 'None') == actual

    value = [1, 1]
    actual = convert_value_to_type(value)
    assert ("list", "int") == actual

    value = [1, None]
    actual = convert_value_to_type(value)
    assert ("list", "int|None") == actual

    value = [1, 'a']
    actual = convert_value_to_type(value)
    assert ("list", "int|str") == actual

    value = [1, ""]
    actual = convert_value_to_type(value)
    assert ("list", "int|str") == actual

    value = [1, "a", 1.0]
    actual = convert_value_to_type(value)
    assert ("list", "float|int|str") == actual

    value = [[]]
    actual = convert_value_to_type(value)
    assert ("list", "list") == actual

    value = [[1]]
    actual = convert_value_to_type(value)
    assert ("list", "list[int]") == actual

    value = [1, [1]]
    actual = convert_value_to_type(value)
    assert ("list", "int|list[int]") == actual

    value = [{1}, {2}]
    actual = convert_value_to_type(value)
    assert ("list", "set[int]") == actual

    value = [{1}, {'a'}]
    actual = convert_value_to_type(value)
    assert ("list", "set[int|str]") == actual

    value = SELF_OR_CLS
    actual = convert_value_to_type(value)
    assert ('self', SELF_OR_CLS) == actual

    value = [1, None]
    actual = convert_value_to_type(value)
    assert ("list", "int|None") == actual

    value = [None, [{1, 'a'}]]
    actual = convert_value_to_type(value)
    assert ("list", "list[set[int|str]]|None") == actual

    # set
    value = set()
    actual = convert_value_to_type(value)
    assert ("set", '') == actual

    value = {1}
    actual = convert_value_to_type(value)
    assert ("set", 'int') == actual

    value = {1, 'a'}
    actual = convert_value_to_type(value)
    assert ("set", 'int|str') == actual

    value = {None, 1, 'a'}
    actual = convert_value_to_type(value)
    assert ("set", 'int|str|None') == actual

    # dict
    value = {}
    actual = convert_value_to_type(value)
    assert ("dict", '') == actual

    value = {'a': 1}
    actual = convert_value_to_type(value)
    assert ("dict", 'str,int') == actual

    value = {None: None}
    actual = convert_value_to_type(value)
    assert ("dict", 'None,None') == actual

    value = {'a': [1]}
    actual = convert_value_to_type(value)
    assert ("dict", 'str,list[int]') == actual

    value = {'a': [1], 'b': ['a']}
    actual = convert_value_to_type(value)
    assert ("dict", 'str,list[int|str]') == actual

    value = {"a": [None, [1]]}
    actual = convert_value_to_type(value)
    assert ("dict", 'str,list[list[int]|None]') == actual

    value = {"a": {1}}
    actual = convert_value_to_type(value)
    assert ("dict", 'str,set[int]') == actual

    value = {"a": {1}, 'b': {2}}
    actual = convert_value_to_type(value)
    assert ("dict", 'str,set[int]') == actual

    value = {None: {None, 1}, 'b': {'a'}}
    actual = convert_value_to_type(value)
    assert ("dict", 'str,set[str]|None,set[int|None]') == actual

    value = {"a": {"b": 1}}
    actual = convert_value_to_type(value)
    assert ("dict", "str,dict[str,int]") == actual

    value = {"a": (1,)}
    actual = convert_value_to_type(value)
    assert ("dict", "str,tuple[int]") == actual

    value = {"a": ({"b": 1},)}
    actual = convert_value_to_type(value)
    assert ("dict", "str,tuple[dict[str,int]]") == actual

    value = {"a": 1, 1: 1}
    actual = convert_value_to_type(value)
    assert ("dict", "int,int|str,int") == actual

    value = {"a": [1, 'a'], 1: [1.0]}
    actual = convert_value_to_type(value)
    assert ("dict", "int,list[float]|str,list[int|str]") == actual

    # tuple
    value = ()
    actual = convert_value_to_type(value)
    assert ("tuple", '') == actual

    value = (None,)
    actual = convert_value_to_type(value)
    assert ("tuple", 'None') == actual

    value = (None, 1)
    actual = convert_value_to_type(value)
    assert ("tuple", 'int|None') == actual

    value = (None, [1])
    actual = convert_value_to_type(value)
    assert ("tuple", 'list[int]|None') == actual

    value = (None, [[1, 'a']])
    actual = convert_value_to_type(value)
    assert ("tuple", 'list[list[int|str]]|None') == actual

    value = (None, (None,))
    actual = convert_value_to_type(value)
    assert ("tuple", 'tuple[None]|None') == actual

    # Callback
    def value(): return None
    actual = convert_value_to_type(value)
    assert ("simple", 'Callable') == actual

    def value(x): return x + 1
    actual = convert_value_to_type(value)
    assert ("simple", 'Callable') == actual

    # class
    value = Foo()
    actual = convert_value_to_type(value)
    assert ("simple", 'Foo') == actual

def test_union_types():
    input = [('class', 'Foo')]
    a = union_types(input)
    assert 'Foo' == a

def test_update_code_with_types_when_default_value_is_none():
    # non None
    input = {'/home/w/repos/typemedaddy/typemedaddy/foo.py:barfoo:65': {'args': {'i': 'int'}, 'return': 'int'}}
    a = update_code_with_types(input)
    assert {'/home/w/repos/typemedaddy/typemedaddy/foo.py:barfoo:65': ('', 'def barfoo (i :int=111 )->int :')} == a
    # None default
    input = {'/home/w/repos/typemedaddy/typemedaddy/foo.py:foobar:62': {'args': {'i': 'int'}, 'return': 'int'}}
    a = update_code_with_types(input)
    assert {'/home/w/repos/typemedaddy/typemedaddy/foo.py:foobar:62': ('', 'def foobar (i :int=None )->int :')} == a

class TestIntegration():

    def test_call_with_class_method(self):
        with trace() as step_1_output:
            f = Foo()
            example_function(1, 2, f)
            example_function(3, 4, None)
            example_function('a', 'b', None)
        for k in step_1_output:
            if "init" in k:
                assert step_1_output[k]["args"] == {
                    "self": [SELF_OR_CLS], "bar": [None]}
                assert step_1_output[k]["return"] == [None]
            elif "example_function" in k:
                assert step_1_output[k]["args"] == {
                    "a": [1, 3, 'a'],
                    "b": [2, 4, 'b'],
                    "foo": [f"USER_CLASS|{MODULE_PATH}::Foo", None, None],
                }
                assert step_1_output[k]["return"] == [3, 7, 'ab']
        print("### out ### \n"*3)
        print(step_1_output)
        # step_1_output = {
        #     '/home/w/repos/typemedaddy/typemedaddy/foo.py:__init__:6':
        #         {'args': {'self': ['SELF_OR_CLS'], 'bar': [None]},
        #          'return': [None]},
        #     '/home/w/repos/typemedaddy/typemedaddy/foo.py:example_function:27':
        #         {'args': {'a': [1, 3, 'a'], 'b': [2, 4, 'b'], 'foo': ['USER_CLASS|typemedaddy.foo::Foo', None, None]},
        #          'return': [3, 7, 'ab']}}
        ##### STEP 2 #####
        step_2_output = convert_results_to_types(step_1_output)
        expected = {'/home/w/repos/typemedaddy/typemedaddy/foo.py:__init__:6': {'args': {'self': ['SELF_OR_CLS'],
                                                                                         'bar': ['None']},
                                                                                'return': ['None']},
                    '/home/w/repos/typemedaddy/typemedaddy/foo.py:example_function:27': {'args': {'a': ['int', 'str'],
                                                                                                  'b': ['int', 'str'],
                                                                                                  'foo': ['Foo', 'None' ]},
                                                                                         'return': ['int', 'str']}}
        assert expected == step_2_output
        ##### STEP 3 #####
        # we generate warnings, no changes to the output data
        ##### STEP 4 - final unify #####
        step_4_output = unify_types_in_final_result(step_2_output)
        expected = {'/home/w/repos/typemedaddy/typemedaddy/foo.py:__init__:6': {'args': {'self': 'SELF_OR_CLS', 'bar': 'None'}, 'return': 'None'},
                    '/home/w/repos/typemedaddy/typemedaddy/foo.py:example_function:27': {'args': {'a': 'int|str',
                                                                                                  'b': 'int|str',
                                                                                                  'foo': 'Foo|None'},
                                                                                         'return': 'int|str'}}
        assert expected == step_4_output
        #### STEP 5 - update code #####
        step_5_output = update_code_with_types(step_4_output)
        expected = {'/home/w/repos/typemedaddy/typemedaddy/foo.py:__init__:6': ('    ', 'def __init__ (self ,bar :None=None )->None :'),
                    '/home/w/repos/typemedaddy/typemedaddy/foo.py:example_function:27': ('', 'def example_function (a :int|str,b :int|str,foo :Foo|None)->int|str :')}
        assert expected == step_5_output
        ##### STEP 6 reformat code #####
        step_6_output = reformat_code(step_5_output)
        expected = {'/home/w/repos/typemedaddy/typemedaddy/foo.py:__init__:6': '    def __init__(self, bar: None = None) -> None:\n',
                    '/home/w/repos/typemedaddy/typemedaddy/foo.py:example_function:27': 'def example_function(a: int | str, b: int | str, foo: Foo | None) -> int | str:\n'}
        assert expected == step_6_output

    # TODO this is a nice-to-do feature where we handle *args,**kwargs
    @pytest.mark.skip
    def test_args_kwargs(self):
        with trace() as step_1_output:
            func_that_takes_any_args([{1}, {'a'}], bar='foo')

    def test_none_type_and_lambda(self):
        f = Foo()
        with trace() as step_1_output:
            example_function(3, 4, None)
            example_function(3, 4, f)
            takes_func_returns_func(lambda: None)
            takes_func_returns_func(1)
        for k in step_1_output:
            if "init" in k:
                assert step_1_output[k]["args"] == {
                    "self": [SELF_OR_CLS], "bar": [None]}
                assert step_1_output[k]["return"] == [None]
            elif "example_function" in k:
                assert step_1_output[k]["args"] == {
                    "a": [3, 3],
                    "b": [4, 4],
                    "foo": [None, 'USER_CLASS|typemedaddy.foo::Foo'],
                }
                assert step_1_output[k]["return"] == [7, 7]
        ##### STEP 2 #####
        step_2_output = convert_results_to_types(step_1_output)
        expected = {'/home/w/repos/typemedaddy/typemedaddy/foo.py:example_function:27': {'args': {'a': ['int'],
                                                                                                  'b': ['int'],
                                                                                                  'foo': ['Foo', 'None']},
                                                                                         'return': ['int']},
                    '/home/w/repos/typemedaddy/typemedaddy/foo.py:takes_func_returns_func:56': {'args': {'callback': ['Callable', 'int'], },
                                                                                                'return': ['Callable', 'int'], },
                    }
        assert expected == step_2_output
        ##### STEP 3 generate warings #####
        ##### STEP 4 - final unify #####
        step_4_output = unify_types_in_final_result(step_2_output)
        expected = {'/home/w/repos/typemedaddy/typemedaddy/foo.py:example_function:27': {'args': {'a': 'int', 'b': 'int', 'foo': 'Foo|None'}, 'return': 'int'}, '/home/w/repos/typemedaddy/typemedaddy/foo.py:takes_func_returns_func:56': {'args': {'callback': 'Callable|int'}, 'return': 'Callable|int'}} 
        assert expected == step_4_output
        ##### STEP 5 #####
        step_5_output = update_code_with_types(step_2_output)
        expected = {
            '/home/w/repos/typemedaddy/typemedaddy/foo.py:example_function:27': ('', 'def example_function (a :int,b :int,foo :Foo|None)->int :'),
            '/home/w/repos/typemedaddy/typemedaddy/foo.py:takes_func_returns_func:56': ('', 'def takes_func_returns_func (callback :Callable|int)->Callable|int :')}
        assert expected == step_5_output
        ##### STEP 6 reformat code #####
        step_6_output = reformat_code(step_5_output)
        expected = {
            '/home/w/repos/typemedaddy/typemedaddy/foo.py:example_function:27': 'def example_function(a: int, b: int, foo: Foo | None) -> int:\n',
            '/home/w/repos/typemedaddy/typemedaddy/foo.py:takes_func_returns_func:56': 'def takes_func_returns_func(callback: Callable | int) -> Callable | int:\n'}
        assert expected == step_6_output

def test_file_update_single_function():
    test_files_dir = "test_files"
    module_name = "module_1"
    from test_files.module_1 import foo
    with trace() as data:
        foo(1)
    assert data
    # rest of steps
    types_data = convert_results_to_types(data)
    unified_types_data = unify_types_in_final_result(types_data)
    updated_function_signatures = update_code_with_types(unified_types_data)
    reformatted_code = reformat_code(updated_function_signatures)
    update_files_with_new_signatures(reformatted_code, backup_file_suffix='bak')
    # verify backup created
    backup_file_path = Path(f"{test_files_dir}/{module_name}.py.bak")
    assert backup_file_path.is_file()
    # verify updated file matches expected
    assert filecmp.cmp(f"{test_files_dir}/{module_name}.py", f"{test_files_dir}/{module_name}.py.expected")
    # clean up backup file
    backup_file_path.unlink()
    # revert original file
    shutil.copy(f"{test_files_dir}/{module_name}.py.orig", f"{test_files_dir}/{module_name}.py")

def test_file_update_two_functions():
    test_files_dir = "test_files"
    module_name = "module_2"
    from test_files.module_2 import foo, bar
    with trace() as data:
        foo(1)
        bar("bob")
    assert data
    # rest of steps
    types_data = convert_results_to_types(data)
    unified_types_data = unify_types_in_final_result(types_data)
    updated_function_signatures = update_code_with_types(unified_types_data)
    reformatted_code = reformat_code(updated_function_signatures)
    update_files_with_new_signatures(reformatted_code, backup_file_suffix='bak')
    # verify backup created
    backup_file_path = Path(f"{test_files_dir}/{module_name}.py.bak")
    assert backup_file_path.is_file()
    # verify updated file matches expected
    assert filecmp.cmp(f"{test_files_dir}/{module_name}.py", f"{test_files_dir}/{module_name}.py.expected")
    # clean up backup file
    backup_file_path.unlink()
    # revert original file
    shutil.copy(f"{test_files_dir}/{module_name}.py.orig", f"{test_files_dir}/{module_name}.py")
