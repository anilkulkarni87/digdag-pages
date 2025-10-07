
from typing import Any, Optional

def maybe_sql_path(val: Any) -> Optional[str]:
    if isinstance(val, str):
        s = val.strip()
        if s.endswith(".sql") or "queries/" in s:
            return s
        return None

    if isinstance(val, dict):
        for k in ("query", "file", "path", "sql", "script"):
            v = val.get(k)
            if isinstance(v, str):
                s = v.strip()
                if s.endswith(".sql") or "queries/" in s:
                    return s
        for v in val.values():
            if isinstance(v, str):
                s = v.strip()
                if s.endswith(".sql") or "queries/" in s:
                    return s

    if isinstance(val, list):
        for v in val:
            p = maybe_sql_path(v)
            if p:
                return p
    return None
