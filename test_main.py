from main import trace
from foo import example_function

# helper fun 
def traverse_dict(d, target, path=None):
    for k,v in d.items():
        full_key = f"{path}|{k}" if path else k
        if k == target:
            return full_key
        if isinstance(v, dict):
            return traverse_dict(v, target, full_key )
    return None

def test_output():
    with trace() as actual:
        example_function(1,2)
    for k in actual:
        assert actual[k]["args"] == {'a': [1], 'b': [2]}
        assert actual[k]["return"] == [3]
