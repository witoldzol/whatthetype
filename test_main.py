from typemedaddy.foo import (
    example_function,
    Foo,
    function_returning_dict,
    int_function,
    returns_a_class,
)
from typemedaddy.typemedaddy import (
    convert_results_to_types,
    convert_value_to_type,
    convert_value_to_type2,
    trace,
    SELF_OR_CLS,
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
        assert actual[k]["args"] == {"self": [SELF_OR_CLS], "name": ["bob"], "age": [9]}
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
    assert sorted(actual["/home/w/repos/typemedaddy/foo.py:int_function:18"]["args"]["a"]) == sorted(["str", "int"])
    assert sorted(actual["/home/w/repos/typemedaddy/foo.py:int_function:18"]["return"]) == sorted(["str", "int"])
    assert sorted(actual["/home/w/repos/typemedaddy/bar.py:bar_function:69"]["args"]["a"]) == sorted(["str", "int"])
    assert sorted(actual["/home/w/repos/typemedaddy/bar.py:bar_function:69"]["return"]) == sorted(["str", "int"])


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

def test_convert_value_to_type2():
    value = 1
    actual = convert_value_to_type2(value)
    assert ("simple", ["int"]) == actual

    value = 'a'
    actual = convert_value_to_type2(value)
    assert ("simple", ["str"]) == actual

    value = 1.0
    actual = convert_value_to_type2(value)
    assert ("simple", ["float"]) == actual

    value = None
    actual = convert_value_to_type2(value)
    assert ("simple", ["None"]) == actual

    value = []
    actual = convert_value_to_type2(value)
    assert ("list", []) == actual

def test_convert_value_to_type():
    value = 1
    actual = convert_value_to_type(value)
    assert "int" == actual

    value = "1"
    actual = convert_value_to_type(value)
    assert "str" == actual

    value = 1.0
    actual = convert_value_to_type(value)
    assert "float" == actual

    value = None
    actual = convert_value_to_type(value)
    assert "None" == actual

    # LIST
    value = []
    actual = convert_value_to_type(value)
    assert "list" == actual

    value = [None]
    actual = convert_value_to_type(value)
    assert "list[None]" == actual

    value = [1]
    actual = convert_value_to_type(value)
    assert "list[int]" == actual

    value = ["a"]
    actual = convert_value_to_type(value)
    assert "list[str]" == actual

    value = SELF_OR_CLS
    actual = convert_value_to_type(value)
    assert SELF_OR_CLS == actual

    value = [1.0]
    actual = convert_value_to_type(value)
    assert "list[float]" == actual

    value = [1, 1]
    actual = convert_value_to_type(value)
    assert "list[int]" == actual

    value = [1, "a"]
    actual = convert_value_to_type(value)
    assert "list[int|str]" == actual

    value = [1, "a", 1.0]
    actual = convert_value_to_type(value)
    assert "list[float|int|str]" == actual

    value = [1, ""]
    actual = convert_value_to_type(value)
    assert "list[int|str]" == actual

    value = [1, None]
    actual = convert_value_to_type(value)
    assert "list[int|None]" == actual

    value = [[]]
    actual = convert_value_to_type(value)
    assert "list[list]" == actual

    value = [[1]]
    actual = convert_value_to_type(value)
    assert "list[list[int]]" == actual

    value = [1, [1]]
    actual = convert_value_to_type(value)
    assert "list[int|list[int]]" == actual

    value = [1, [1, [1]]]
    actual = convert_value_to_type(value)
    assert "list[int|list[int|list[int]]]" == actual

    value = [None, [1, [1]]]
    actual = convert_value_to_type(value)
    assert "list[list[int|list[int]]|None]" == actual

    value = set()
    actual = convert_value_to_type(value)
    assert "set" == actual

    value = {1}
    actual = convert_value_to_type(value)
    assert "set[int]" == actual

    value = {1, "a"}
    actual = convert_value_to_type(value)
    assert "set[int|str]" == actual

    value = [{1, "a"}]
    actual = convert_value_to_type(value)
    assert "list[set[int|str]]" == actual

    value = [None, [{1, "a"}]]
    actual = convert_value_to_type(value)
    assert "list[list[set[int|str]]|None]" == actual

    value = {}
    actual = convert_value_to_type(value)
    assert "dict" == actual

    value = {None: None}
    actual = convert_value_to_type(value)
    assert "dict[None,None]" == actual

    value = {"a": 1}
    actual = convert_value_to_type(value)
    assert "dict[str,int]" == actual

    value = {"a": [1]}
    actual = convert_value_to_type(value)
    assert "dict[str,list[int]]" == actual

    value = {"a": [None, [1]]}
    actual = convert_value_to_type(value)
    assert "dict[str,list[list[int]|None]]" == actual

    value = {"a": {1}}
    actual = convert_value_to_type(value)
    assert "dict[str,set[int]]" == actual

    value = {"a": {1}, "b": {2}}
    actual = convert_value_to_type(value)
    assert "dict[str,set[int]]" == actual

    value = {"a": {1}, "b": {1}}
    actual = convert_value_to_type(value)
    assert "dict[str,set[int]]" == actual

    value = {None: {None, 1}, "b": {"a"}}
    actual = convert_value_to_type(value)
    assert "dict[None,set[int|None]|str,set[str]]" == actual

    value = {"a": {"b": 1}}
    actual = convert_value_to_type(value)
    assert "dict[str,dict[str,int]]" == actual

    value = {"a": (1,)}
    actual = convert_value_to_type(value)
    assert "dict[str,tuple[int]]" == actual

    value = {"a": ({"b": 1},)}
    actual = convert_value_to_type(value)
    assert "dict[str,tuple[dict[str,int]]]" == actual

class TestIntegration():

    def test_call_with_class_method(self):
        with trace() as step_1_output:
            f = Foo()
            example_function(1, 2, f)
            example_function(3, 4, None)
            example_function('a', 'b', None)
        for k in step_1_output:
            if "init" in k:
                assert step_1_output[k]["args"] == {"self": [SELF_OR_CLS], "bar": [None]}
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
        #     '/home/w/repos/typemedaddy/typemedaddy/foo.py:example_function:25': 
        #         {'args': {'a': [1, 3, 'a'], 'b': [2, 4, 'b'], 'foo': ['USER_CLASS|typemedaddy.foo::Foo', None, None]},
        #          'return': [3, 7, 'ab']}}
        ##### STEP 2 #####
        step_2_output = convert_results_to_types(step_1_output)
        expected = {'/home/w/repos/typemedaddy/typemedaddy/foo.py:__init__:6': {'args': {'self': ['SELF_OR_CLS'],
                                                                                         'bar': ['None']},
                                                                                'return': ['None']},
                    '/home/w/repos/typemedaddy/typemedaddy/foo.py:example_function:25': {'args': {'a': ['int', 'str'],
                                                                                                  'b': ['int', 'str'],
                                                                                                  'foo': ['None',
                                                                                                          'str']},
                                                                                         'return': ['int', 'str']}}
        assert expected == step_2_output
        ##### STEP 3 #####
        # step_3_output = update_code_with_types(step_2_output)
        # print("### integration ### \n"*3)
        # print(step_3_output)
        # expected = {'/home/w/repos/typemedaddy/typemedaddy/foo.py:__init__:6': '    def __init__ (self ,bar :None=None ):\n', '/home/w/repos/typemedaddy/typemedaddy/foo.py:example_function:25': "def example_function (a :['int'|'str'],b :['int'|'str'],foo :['str'|'None']):\n"}

    def test_repeated_calls(self):
        with trace() as step_1_output:
            example_function(1, 2, None)
            example_function(3, 4, None)
            example_function('a', 'b', None)
        for k in step_1_output:
            if "example_function" in k:
                assert step_1_output[k]["args"] == {
                    "a": [1, 3, 'a'],
                    "b": [2, 4, 'b'],
                    "foo": [None,None,None]
                }
                assert step_1_output[k]["return"] == [3, 7, 'ab']
        ##################
        ##### STEP 2 #####
        ##################
        step_2_output = convert_results_to_types(step_1_output)
        expected = {'/home/w/repos/typemedaddy/typemedaddy/foo.py:example_function:25': {'args': {'a': ['int','str'],
                                                                                                  'b': ['int','str'],
                                                                                                  'foo': ['None']},
                                                                                         'return': ['int','str']}}
        assert expected == step_2_output
        ##################
        ##### STEP 3 #####
        ##################
        # step_3_output = update_code_with_types(step_2_output)
        # print("### integration ### \n"*3)
        # print(step_3_output)
        # for k in step_3_output:
        #     if 'example_function' in k:
        #         expected = "def example_function (a :['int'|'str'],b :['int'|'str'],foo :['str'|'None']):\n"
        #         assert expected == step_3_output[k]

    # def test_none_type(self):
    #     with trace() as step_1_output:
    #         example_function(3, 4, None)
    #         example_function(3, 4, None)
    #     for k in step_1_output:
    #         if "init" in k:
    #             assert step_1_output[k]["args"] == {"self": [SELF_OR_CLS], "bar": [None]}
    #             assert step_1_output[k]["return"] == [None]
    #         elif "example_function" in k:
    #             assert step_1_output[k]["args"] == {
    #                 "a": [3, 3],
    #                 "b": [4, 4],
    #                 "foo": [None, None],
    #             }
    #             assert step_1_output[k]["return"] == [7, 7]
    #     ##### STEP 2 #####
    #     step_2_output = convert_results_to_types(step_1_output)
    #     expected = {'/home/w/repos/typemedaddy/typemedaddy/foo.py:example_function:25': {'args': {'a': ['int'],
    #                                                                                               'b': ['int'],
    #                                                                                               'foo': ['None']},
    #                                                                                      'return': ['int']}}
    #     assert expected == step_2_output
    #     ##### STEP 3 #####
    #     step_3_output = update_code_with_types(step_2_output)
    #     print("### integration ### \n"*3)
    #     print(step_3_output)
    #     expected = {'/home/w/repos/typemedaddy/typemedaddy/foo.py:__init__:6': '    def __init__ (self ,bar :None=None ):\n', '/home/w/repos/typemedaddy/typemedaddy/foo.py:example_function:25': "def example_function (a :['int'|'str'],b :['int'|'str'],foo :['str'|'None']):\n"}

def test_bob():
    value = {"a": {1}, "b": {"a"}}
    actual = convert_value_to_type(value)
    assert "dict[str,set[int|str]]" == actual

    # value = {"a": {None, 1}, "b": {"a"}}
    # actual = convert_value_to_type(value)
    # assert "dict[str,set[int|str|None]]" == actual
    #
    # value = {"a": {None, 1}, "b": {"a"}}
    # actual = convert_value_to_type(value)
    # assert "dict[str,set[int|str|None]]" == actual

# def test_unify_types():
#     input = ['set[int]','set[str]']
#     a = unify_types(input)
#     e = ['set[int|str]']
