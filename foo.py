from random import choice
from nested.inner.bar import Bar


class Foo:
    def __init__(self, bar: Bar = None):
        self.bar = bar

    def get_foo(self, name, age):
        return f"{name},{age}"


def example_function_with_third_party_lib(a, b):
    r = choice([a, b])
    return r


def example_function(a, b, foo):
    if type(a) is str and type(b) is int:
        a = int(a)
    return a + b


def function_returning_dict():
    a = {}
    a["value"] = 1
    a["foo"] = {}
    a["foo"]["bar"] = 2
    return a


def function_taking_nested_class(bar: Bar):
    return bar.name


def function_calling_nested_functions():
    function_returning_dict()

def returns_a_class():
    f = Foo()
    return f
