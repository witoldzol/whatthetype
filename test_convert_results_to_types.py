from main import convert_results_to_types

def test_empty_result():
    r = convert_results_to_types({})
    assert r == {}
