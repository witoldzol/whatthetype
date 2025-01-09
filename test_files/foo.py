from random import choice
from typing import Union
from test_files.nested.inner.bar import Bar

class Foo:
    def __init__(self, bar: Bar=None):
        self.bar = bar

    def get_foo(self, name, age):
        return f"{name},{age}"

    def arbitrary_self(not_self, name: str = 'default_val', age=10):
        not_self.bar = 'lol'
        return f"{name},{age}"
    
    def args_kwargs_func(self, *args, **kwargs):
        return 'lol'

def example_function_with_third_party_lib(a, b):
    r = choice([a, b])
    return r


def int_function(i) -> int:
    return i

def example_function(a, b, foo):
    if type(a) is str and type(b) is int:
        a = int(a)
    return a + b

def func_that_takes_any_args(*args, **kwargs):
    return len(args) + len(kwargs)

def function_returning_dict():
    return {
        "foo": {
            "bar": 2,
        },
        "value": 1,
    }


def function_taking_nested_class(bar):
    return bar.name


def function_calling_nested_functions():
    function_returning_dict()


def returns_a_class():
    f = Foo()
    return f

def takes_func_returns_func(callback):
    return callback

def takes_class(f: Foo):
    return 1

def foobar(i:int = None) -> int:
    return i

def barfoo(i:int = 111) -> int:
    return i

class MultiLine():
    def __init__(self,
                 a,
                 b,
                 c):
        pass

class MultiLineSeparateBracket():
    def __init__(self,
                 a,
                 b,
                 c
                 ):
        pass
