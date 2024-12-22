# How to use
```python
from typemedaddy.typemedaddy import trace, type_it_like_its_hot

def foo(i,
        x):
    return {'a': [(i + x,)]}

with trace() as data:
    foo(11, 2)
type_it_like_its_hot(data, update_files=True, backup_file_suffix=None, dump_intermediate_data=False)
```

# Result
```python
from typemedaddy.typemedaddy import trace, type_it_like_its_hot

def foo(i: int,
        x: int) -> dict[str, list[tuple[int]]]:
    return {'a': [(i + x,)]}

with trace() as data:
    foo(11, 2)
type_it_like_its_hot(data, update_files=True, backup_file_suffix=None, dump_intermediate_data=False)
```

# CAUTION!!!
This lib will OVERWRITE YOUR SOURCE FILES! ( It creates backup files before it does )
Use SOURCE CONTROL before running this !!!!

# What
Inspects code at runtime, derives types from arguments and updates in-place source files with detected type hints and required imports.

# Requirements
At minimum 3.5 - I haven't tested properly.
Ideally use 3.9 or higher ( This lib supports both Union and '|' operators)

# Install
```bash
pip install typemedaddy
```

# Params
```python
""" params
update_files: updates source files in place with new types, this is a destructive action! 
            If False, results json will be saved to a file with unix timestamp. 
            Default = False.
backup_file_suffix: creates backup files and adds suffix to them.
            Example: backup_file_suffix="bak" will create `foo.py.bak`. 
            Default = "bak"
dump_intermediate_data: will create 3 files with intermediate data used to derive final results. 
            Default = False
"""
```
