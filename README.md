# CAUTION!!!
This lib will OVERWRITE YOUR SOURCE FILES! ( It creates backup files before it does )
Use SOURCE CONTROL before running this !!!!

This is a hobby project, not a production ready stuff.
I'm not a 'good' programmer - no classes or clean code over here, just procedural spaghetti.

# WHAT?
This lib can inspect the data passed to your functions, figure out types from that data and update your function signatures with type info.

# WHY?
I maintain a legacy project that has no typing at all. 
It's thousands of lines of code and I have no idea what goes in or out.
This is my feeble attemt to remedy this problem automagically.

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

with trace() as trace_data:
    your_script()
type_it_like_its_hot(trace_data, update_files = True, backup_file_suffix = "bak")
```

# Notes to myself
## Build
`python setup.py bdist_wheel && rm -rf build && rm -rf *egg-info`
## Publish
`twine dist/*`
token is defined in `$HOME/.pypirc`
