import logging
from typemedaddy.typemedaddy import trace, type_it_like_its_hot


logging.basicConfig(level=logging.DEBUG)

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


with trace() as data:
    kfoo(11, 'a', None)
type_it_like_its_hot(data, update_files=True, backup_file_suffix=None)
