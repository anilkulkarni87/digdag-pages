from digdaggraph.sql_extract import maybe_sql_path

def test_maybe_sql_path_basic():
    assert maybe_sql_path("queries/foo.sql") == "queries/foo.sql"
    assert maybe_sql_path({"file": "queries/bar.sql"}) == "queries/bar.sql"
    assert maybe_sql_path({"x": {"y": "queries/x/y.sql"}}) == "queries/x/y.sql"
    assert maybe_sql_path(["a", {"path":"queries/z.sql"}]) == "queries/z.sql"
    assert maybe_sql_path("not_sql.txt") is None
