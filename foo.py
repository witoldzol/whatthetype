from nested.inner.bar import Bar

class Foo:
    def __init__(self, bar: Bar = None):
        self.bar = bar

    def get_foo(self, name, age):
        return f"Foo({name}, {age})"


def example_function(a, b, foo):
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
