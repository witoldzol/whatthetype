from typemedaddy.foo39 import example_function, Foo
from typemedaddy.typemedaddy import (
    trace,
    SELF_OR_CLS,
    unify_types_in_final_result,
    convert_results_to_types,
    update_code_with_types,
    reformat_code,
    union_types,
)

MODULE_PATH = "typemedaddy.foo39"


def test_union_types():
    input = [("class", "Foo")]
    a = union_types(input)
    assert "Foo" == a


def test_call_with_class_method_39():
    with trace() as step_1_output:
        f = Foo()
        example_function(1, 2, f)
        example_function(3, 4, None)
        example_function("a", "b", None)
    for k in step_1_output:
        if "init" in k:
            assert step_1_output[k]["args"] == {"self": [SELF_OR_CLS], "bar": [None]}
            assert step_1_output[k]["return"] == [None]
        elif "example_function" in k:
            assert step_1_output[k]["args"] == {
                "a": [1, 3, "a"],
                "b": [2, 4, "b"],
                "foo": [f"USER_CLASS|{MODULE_PATH}::Foo", None, None],
            }
            assert step_1_output[k]["return"] == [3, 7, "ab"]
    print("### out ### \n" * 3)
    print(step_1_output)
    # step_1_output = {
    #     '/home/w/repos/typemedaddy/typemedaddy/foo39.py:__init__:4':
    #         {'args': {'self': ['SELF_OR_CLS'], 'bar': [None]},
    #          'return': [None]},
    #     '/home/w/repos/typemedaddy/typemedaddy/foo39.py:example_function:17':
    #         {'args': {'a': [1, 3, 'a'], 'b': [2, 4, 'b'], 'foo': ['USER_CLASS|typemedaddy.foo39::Foo', None, None]},
    #          'return': [3, 7, 'ab']}}
    ##### STEP 2 #####
    step_2_output = convert_results_to_types(step_1_output)
    expected = {
        "/home/w/repos/typemedaddy/typemedaddy/foo39.py:__init__:4": {
            "args": {"self": ["SELF_OR_CLS"], "bar": ["None"]},
            "return": ["None"],
        },
        "/home/w/repos/typemedaddy/typemedaddy/foo39.py:example_function:17": {
            "args": {"a": ["int", "str"], "b": ["int", "str"], "foo": ["Foo", "None"]},
            "return": ["int", "str"],
        },
    }
    assert expected == step_2_output
    ##### STEP 3 #####
    # we generate warnings, no changes to the output data
    ##### STEP 4 - final unify #####
    step_4_output = unify_types_in_final_result(step_2_output)
    expected = {
        "/home/w/repos/typemedaddy/typemedaddy/foo39.py:__init__:4": {
            "args": {"self": "SELF_OR_CLS", "bar": "None"},
            "return": "None",
        },
        "/home/w/repos/typemedaddy/typemedaddy/foo39.py:example_function:17": {
            "args": {"a": "Union[int, str]", "b": "Union[int, str]", "foo": "Union[Foo, None]"},
            "return": "Union[int, str]",
        },
    }
    assert expected == step_4_output
    #### STEP 5 - update code #####
    step_5_output = update_code_with_types(step_4_output)
    expected = {
        "/home/w/repos/typemedaddy/typemedaddy/foo39.py:__init__:4": (
            "    ",
            "def __init__ (self ,bar :None=None )->None :",
        ),
        "/home/w/repos/typemedaddy/typemedaddy/foo39.py:example_function:17": (
            "",
            "def example_function (a :Union[int, str],b :Union[int, str],foo :Union[Foo, None])->Union[int, str] :",
        ),
    }
    assert expected == step_5_output
    ##### STEP 6 reformat code #####
    step_6_output = reformat_code(step_5_output)
    expected = {
        "/home/w/repos/typemedaddy/typemedaddy/foo39.py:__init__:4": "    def __init__(self, bar: None = None) -> None:\n",
        "/home/w/repos/typemedaddy/typemedaddy/foo39.py:example_function:17": "def example_function(a: Union[int, str], b: Union[int, str], foo: Union[Foo, None]) -> Union[int, str]:\n",
    }
    assert expected == step_6_output
