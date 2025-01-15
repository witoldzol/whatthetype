from whatthetype.nested.inner.bar import Bar

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

def example_function(a, b, foo) -> int:
    if type(a) is str and type(b) is int:
        a = int(a)
    return a + b
