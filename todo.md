# identify 'self' & 'cls' aka first arg of class method, and give it 'special' arg,
so that we can skip it in 3rd step when we are upating function defs!
or identify if method or free funct using `inspect` module & `ismethod()` or `isfunction()`
```python
class Foo():
    def bob(omg, wow):
        return wow
result = {
    'module_function_line': {
        'args': {
            'omg': ['SELF_OR_CLS'],
            'wow': ['str']
        },
        'return': ['str']
    }
}
```
# implement replacement algo:
- get index of start and end of ()
- extract everything between brackets
- split by comma
- check if type exists -> split by ':', if yes, drop it?
    - if type is 'SELF_OR_CLS', skip, we add nothing, just reinsert arg as it was
- check if default value exists -> split by '=', if yes, save it somewhere
- add new types
- add existing default values
- insert new stuff + everything that was after end of ')'
# should we use python 3.12 monitoring api?
# make sure we presever order of arguments! 
# CLI: add arguments to run step 1 / 2 / 3 ?
# create a warning if an argument in a function takes two or more different types of input
foo(int|str) : this might be an indication of a bug
# save step 1 output to a file?
