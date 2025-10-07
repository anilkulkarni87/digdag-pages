from digdaggraph.yaml_includes import resolve_includes

def test_resolve_list_passthrough():
    assert resolve_includes([1,2,3]) == [1,2,3]
