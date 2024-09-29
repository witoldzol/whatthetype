# add tests around self ref object
# implement replacement algo:
- get index of start and end of ()
- extract everything between brackets
- split by comma
- check if type exists -> split by ':', if yes, drop it?
    - if type is 'SELF_OR_CLS', skip, we add nothing, remove the type, just reinsert arg
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


## DONE ##
# identify 'self' & 'cls' aka first arg of class method, and give it 'special' arg,
so that we can mark it as `SELF_OR_CLS`
why? so we can skip in further steps, THIS IS NOT STRICTLY NECESSARY, but it's 'best' for completion sake to capture all args, even self refrences
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
