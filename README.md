# How to publish to twine
`twine dist/*`
token is defined in `$HOME/.pypirc`

# Aim
To autogenerate type hints

# Description
Trace runtime and collect information on all arguments passed to functions.
Same for return values.
Second part of this project will take the collected data and will generate a list of all types based on the values it saw.
Final part will update existing code with the type notations based on what was discovered in second step.

# How to use
```python
from typemedaddy.typemedaddy import trace

with trace():
    my_script()
```
