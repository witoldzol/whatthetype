class Foo:
    def __init__(self, bar = None):
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
