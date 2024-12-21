# CAUTION!!!
This lib will OVERWRITE YOUR SOURCE FILES! ( It creates backup files before it does )
Use SOURCE CONTROL before running this !!!!

# WHAT?
This lib can inspect the data passed to your functions, figure out types from that data and update your function signatures with type info.

# WHY?
I maintain a legacy project that has no type hints at all. 
It's thousands of lines of code and I have no idea what goes in or out.
This lib can create type hints on the fly.

# REQUIREMENTS
At minimum 3.5 - I haven't tested properly.
Ideally use 3.9 or higher ( This lib supports both Union and '|' )

# INSTALL
```bash
pip install typemedaddy
```

# HOW?
```python
from typemedaddy.typemedaddy import trace, type_it_like_its_hot

def foo(i, x):
    return i + x

with trace() as data:
    foo(1, 2)

"""
update_files: updates source files in place with new types, this is a destructive action! 
            If False, results json will be saved to a file with unix timestamp. 
            Default = False.
backup_file_suffix: creates backup files and adds suffix to them.
            Example: backup_file_suffix="bak" will create `foo.py.bak`. 
            Default = "bak"
dump_intermediate_data: will create 3 files with intermediate data used to derive final results. 
            Default = False
"""
type_it_like_its_hot(data, update_files=True, backup_file_suffix="bak", dump_intermediate_data=False)
```

# Notes to myself
## Build
`python setup.py bdist_wheel && rm -rf build && rm -rf *egg-info`
## Publish
`twine dist/*`
token is defined in `$HOME/.pypirc`
