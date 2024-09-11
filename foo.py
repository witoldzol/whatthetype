# import contextlib
from random import choice
from nested.inner.bar import Bar

class Foo:
    def __init__(self, bar: Bar = None):
        self.bar = bar

    def get_foo(self, name, age):
        return f"Foo({name}, {age})"


def example_function_with_third_party_lib(a,b):
    r = choice([a,b])
    return r

def example_function(a, b, foo):
    if type(a) is str:
        a = int(a)
    c = a + b
    return c

def function_returning_dict():
    a = {}
    a['value'] = 1
    a['foo'] = {}
    a['foo']['bar'] = 2
    return a

def function_taking_nested_class(bar: Bar):
    return bar.name

# @contextlib.contextmanager
# def trace():
#     global RESULT
#     print("========== TRACING ON ==========")
#     sys.settrace(trace_function)
#     try:
#         yield RESULT
#     finally:
#         print("========== TRACING OFF ==========")
#         sys.settrace(None)
#         RESULT = {}
