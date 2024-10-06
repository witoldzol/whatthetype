# fix union of types
# put None at the end if union of types
# implement replacement algo:
- split lines into tokens
- detect start and end of arguments
- analyze each argument:
-- does it have a type
-- does it have a default value?
-- add type if not there
- when done, un-tokenize and you have a string representing function !
## edge case - what about multiline function signatures?
# should we deduplicate inputs from step 1? the data set will grow crazy big, and it will make step 2 work much harder ( although, we do have dedup in step 2...)
# should we use python 3.12 monitoring api?
# make sure we presever order of arguments! 
# CLI: add arguments to run step 1 / 2 / 3 ?
# create a warning if an argument in a function takes two or more different types of input
foo(int|str) : this might be an indication of a bug
# save step 1 output to a file?








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
