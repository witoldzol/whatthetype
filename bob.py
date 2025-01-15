import logging
from whatthetype.whatthetype import trace, type_it_like_its_hot


logging.basicConfig(level=logging.INFO)

def decorator_one(f):
    def wrapper(i, x):
        print('im other wrapper')
        f(i, x)
    return wrapper

def decorator_two(f):
    def wrapper(i, x):
        print('im a wrapper')
        f(i, x)
    return wrapper


def bar(i, x ):
    return i

@decorator_two
@decorator_one
def foo(i, 
        x = 'x'):
    return i

def kfoo(*args):
    return (*args,)

def kwfoo(*args, 
          **kwargs
          ):
    print('a')
    return 'kwfoo'


def all_at_once(name, 
                age = 69, 
                *args, 
                **kwargs
                ):
    print(name)
    print(age)
    print(args)
    print(kwargs)
    return {'all_at_once'}

def oneline(a): return a + 1

with trace() as data:
    kfoo(11, 'a', None)
    kwfoo(1, 'a', {'a': 1, 'b': 2})
    all_at_once('bob', 66, 1, 'a', {'a': 1, 'b': 2})
    oneline(9)
type_it_like_its_hot(data, update_files=True, backup_file_suffix=None)
