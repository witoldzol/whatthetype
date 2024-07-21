from main import trace
from foo import example_function, Foo

# helper fun 
def traverse_dict(d, target, path=None):
    for k,v in d.items():
        full_key = f"{path}|{k}" if path else k
        if k == target:
            return full_key
        if isinstance(v, dict):
            return traverse_dict(v, target, full_key )
    return None

def test_example_function():
    with trace() as actual:
        f = Foo()
        example_function(1,2, f)
        print(actual)
        print("="*100)
    for k in actual:
        assert actual[k]["args"] == {'a': ['int'], 'b': ['int'], 'foo': ['Foo']}
        assert actual[k]["return"] == ['int']

def test_if_global_context_is_not_polluted_by_previous_test_invocation():
    with trace() as actual:
        f = Foo()
        example_function(1,2, f)
        print(actual)
        print("="*100)
    for k in actual:
        assert actual[k]["args"] == {'a': ['int'], 'b': ['int'], 'foo': ['Foo']}
        assert actual[k]["return"] == ['int']

# def test_example_function_with_different_args():
#     with trace() as actual:
#         f = Foo()
#         example_function(1,2, f)
#         example_function("bob","wow", f)
#     for k in actual:
#         print(actual)
#         assert actual[k]["args"] == {'a': ['int'], 'b': ['int'], 'foo': ['Foo']}
#         assert actual[k]["return"] == ['int']


# todo - test same func called with different args

# def test_class_method():
#     f = Foo()
#     with trace() as actual:
#         f.get_foo("bob",9)
#     for k in actual:
#         assert actual[k]["args"] == {'name': ["foo"], 'age': [2]}
#         assert actual[k]["return"] == [3]
