from typemedaddy.foo39 import example_function, Foo
from typemedaddy.typemedaddy import trace, SELF_OR_CLS, convert_value_to_type, unify_types_in_final_result, convert_results_to_types, update_code_with_types, reformat_code, union_types

# UNION_OPERATOR = lambda x: f"Union[{', '.join(x)}]" if len(x) > 1 else str(x)

def test_union_types():
    input = [('class', 'Foo')]
    a = union_types(input)
    assert 'Foo' == a

def test_python_35_39():
    with trace() as step_1_output:
        f = Foo()
        example_function(3, 4, None)
        example_function(3, 4, f)
        for k in step_1_output:
            if "init" in k:
                assert step_1_output[k]["args"] == {
                    "self": [SELF_OR_CLS], "bar": [None]}
                assert step_1_output[k]["return"] == [None]
            elif "example_function" in k:
                print("><"*100)
                print(step_1_output[k]["args"])
                print("><"*100)
                assert step_1_output[k]["args"] == {
                    "a": [3, 3],
                    "b": [4, 4],
                    "foo": [None, 'USER_CLASS|typemedaddy.foo39::Foo'],
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
    expected = {'/home/w/repos/typemedaddy/typemedaddy/foo.py:example_function:27': {'args': {'a': 'int', 'b': 'int', 'foo': 'Union[Foo, None]'}, 'return': 'int'}, '/home/w/repos/typemedaddy/typemedaddy/foo.py:takes_func_returns_func:56': {'args': {'callback': '[Callable, int]'}, 'return': 'Union[Callable, int]'}} 
    assert expected == step_4_output
    ##### STEP 5 #####
    step_5_output = update_code_with_types(step_2_output)
    expected = {
        '/home/w/repos/typemedaddy/typemedaddy/foo.py:example_function:27': ('', 'def example_function (a :int,b :int,foo :Union[Foo, None])->int :'),
        '/home/w/repos/typemedaddy/typemedaddy/foo.py:takes_func_returns_func:56': ('', 'def takes_func_returns_func (callback :Union[Callable, int])->Union[Callable, int] :')}
    assert expected == step_5_output
    ##### STEP 6 reformat code #####
    step_6_output = reformat_code(step_5_output)
    expected = {
        '/home/w/repos/typemedaddy/typemedaddy/foo.py:example_function:27': 'def example_function(a: int, b: int, foo: Union[Foo, None]) -> int:\n',
        '/home/w/repos/typemedaddy/typemedaddy/foo.py:takes_func_returns_func:56': 'def takes_func_returns_func(callback: Union[Callable, int]) -> Union[Callable, int]:\n'}
    assert expected == step_6_output
