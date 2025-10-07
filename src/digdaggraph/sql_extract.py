from typing import Any, Optional

# Keys commonly used to hold a SQL file path in Digdag/td> task shapes
SQL_HINT_KEYS = ("query", "file", "path", "sql", "script")


def _looks_like_sql_path(s: str) -> bool:
    """
    Heuristic: treat a string as a SQL path if it ends with .sql or
    contains a 'queries/' segment (preserves nested subfolders).
    """
    s = s.strip()
    return s.endswith(".sql") or "queries/" in s


def maybe_sql_path(val: Any) -> Optional[str]:
    """
    Heuristically find a SQL path inside strings / dicts / lists, recursing deeply.

    Returns the first match found (preorder). Does not touch the filesystem.
    Examples it should handle:
      - "queries/foo.sql"
      - {"file": "queries/bar.sql"}
      - {"x": {"y": "queries/x/y.sql"}}
      - ["a", {"path": "queries/z.sql"}]
    """
    # String
    if isinstance(val, str):
        return val.strip() if _looks_like_sql_path(val) else None

    # Dict: check common keys first, then any direct string values, then recurse
    if isinstance(val, dict):
        # 1) common keys
        for k in SQL_HINT_KEYS:
            v = val.get(k)
            if isinstance(v, str) and _looks_like_sql_path(v):
                return v.strip()

        # 2) any direct string values
        for v in val.values():
            if isinstance(v, str) and _looks_like_sql_path(v):
                return v.strip()

        # 3) recurse into child containers
        for v in val.values():
            found = maybe_sql_path(v)
            if found:
                return found
        return None

    # List / tuple: recurse over items
    if isinstance(val, (list, tuple)):
        for v in val:
            found = maybe_sql_path(v)
            if found:
                return found
        return None

    # Anything else
    return None
