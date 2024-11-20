# handle multi line function signatures
# CLI: add arguments to run steps?
# update readme
## edge case - what about multiline function signatures?
- use tokenize to figure out if the func sig is multi line
# make sure we presever order of arguments! 
# save step 1 output to a file?

==============================================================================================
======================================== NICE TO DO ? ========================================
==============================================================================================
# implement no union operator
# should we deduplicate inputs from step 1? the data set will grow crazy big, and it will make step 2 work much harder ( although, we do have dedup in step 2...)
# should we use python 3.12 monitoring api?
# refactor update_code_with_types
maybe use separate passes where we handle args and return types/values
this would greatly simplyfy the necessary logic
# handle *args and **kwargs
- args and kwargs can be called whatever you want, so it's the same issue as with 'self' ref
- both stand alone functions and class methods can have *args 
- do we care? Not yet!
looks like tracing *args results in args that have no name...which makes sense
how will we handle that?


############################################################
## DONE ##
############################################################
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
# add tests around self ref object
# add test case where we trace same function twice, and verify we don't store duplicate types
# convert 'NoneType' to 'None' ( step 2 or 3 ????)
# fix union of types
## expectations
```python
value = {"a": {None}, "b": {"a"}}
actual = convert_value_to_type(value)
assert "dict[str,set[str|None]]" == actual
```
## reality
```python
value = {"a": {1}, "b": {"a"}}
actual = convert_value_to_type(value)
assert "dict[str,set[int|str]]" == actual
AssertionError: assert 'dict[str,set[int|str]]' == 'dict[str,set...str,set[str]]'

  - dict[str,set[int]|str,set[str]]
  ?                 - --------
  + dict[str,set[int|str]]
```
## what about 
value = [{1},{'a'}] ??
should it be list[set[int|str]] ? or list[set[int]|set[str]] ??
## final decision
I will leave it as
pyright didn't complain about either:
```python
l = [{1}, {'a'}]
def foo(l: list[set[int|str]]) -> int:
def foo(l: list[set[int]|set[str]]) -> int:
```
# put None at the end if union of types
# in step 2 end, unify results array
at the moment convert_results_to_types will return an array of types per function argument
we defo want to 'unify' those results into one, so that step 3 can just update with one arg?
OR, we add a new step
BECAUSE if we have an array of multiple results, that's an easy way to identify an arg that takes in multple 
DIFFERENT types ( which is probably an BUG or potential issue )
# test collables as args and as return types
# in step 5 - when you detect a pre existing type, there can be MULTIPLE of them - test & handle this case
at the moment we are dropping first detected type
```bash
OLD
def example_function(a: float|bool, b, foo):
>>>>>>>>>>
NEW
def example_function (a :int|str|bool ,b :int|str,foo :str|None):
```
# implement replacement algo
# deal with user classes types
# fix default value missing when original function has type and default value set to None
```python
# before
def foobar(i:int = None) -> int:
    return i
# after tokenizing
def foobar (i :int=)->int :
```
# usedefault in dictionaries to simplyfy logic 
# generate warnings if arg takes two or more types of data
# reformat updated function definitions to make it nice
# update actual files with the new code and create .bak files
# when upating files, build a list of modules, and updated them in a batch
# new  stage - generate imports
# fix indentation issue - __init__ method doesn't get indented properly
# implement python 3.5 <= and => 3.9 union types ( Union[] )
# add Union imports
