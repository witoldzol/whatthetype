from main import trace
from foo import example_function, Foo, function_returning_dict


# helper fun
def traverse_dict(d, target, path=None):
    for k, v in d.items():
        full_key = f"{path}|{k}" if path else k
        if k == target:
            return full_key
        if isinstance(v, dict):
            return traverse_dict(v, target, full_key)
    return None


def test_example_function():
    with trace() as actual:
        f = Foo()
        example_function(1, 2, f)
    for k in actual:
        if 'init' in k:
            assert actual[k]["args"] == {"bar": {"NoneType"}}
        elif 'get_foo' in k:
            assert actual[k]["args"] == {"a": {"int"}, "b": {"int"}, "foo": {"Foo"}}
            assert actual[k]["return"] == {"int"}


def test_if_global_context_is_not_polluted_by_previous_test_invocation():
    with trace() as actual:
        f = Foo()
        example_function(1, 2, f)
    for k in actual:
        if 'init' in k:
            assert actual[k]["args"] == {"bar": {"NoneType"}}
        elif 'get_foo' in k:
            assert actual[k]["args"] == {"a": {"int"}, "b": {"int"}, "foo": {"Foo"}}
            assert actual[k]["return"] == {"int"}


def test_example_function_with_different_args():
    with trace() as actual:
        f = Foo()
        example_function(1, 2, f)
        example_function("bob", "wow", f)
    for k in actual:
        if 'init' in k:
            assert actual[k]["args"] == {"bar": {"NoneType"}}
        elif 'get_foo' in k:
            assert actual[k]["args"] == {
                "a": {"int", "str"},
                "b": {"int", "str"},
                "foo": {"Foo"},
            }
            assert actual[k]["return"] == {"int", "str"}


def test_class_method():
    f = Foo()
    with trace() as actual:
        f.get_foo("bob", 9)
    for k in actual:
        assert actual[k]["args"] == {"name": {"str"}, "age": {"int"}}
        assert actual[k]["return"] == {"str"}

def test_function_returning_dict():
    with trace() as actual:
        function_returning_dict()
    for k in actual:
        assert actual[k]["args"] == {}
        assert actual[k]["return"] == {"dict"}
