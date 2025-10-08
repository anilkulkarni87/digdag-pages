from __future__ import annotations

from typing import Any, Dict, Optional

def normalize_retry(v: Any) -> Optional[Dict[str, Any]]:
    """
    Accept Digdag `_retry` in its common shapes and return a normalized dict:
      - int -> {"limit": int}
      - str (e.g., "3") -> {"limit": int}
      - mapping -> copy keys we understand (limit, interval, max_interval, type)
    Returns None if v is falsy or unrecognized.
    """
    if v is None:
        return None
    if isinstance(v, bool):
        # Digdag doesn't use boolean for retry; ignore
        return None
    if isinstance(v, int):
        return {"limit": v}
    if isinstance(v, str):
        try:
            return {"limit": int(v)}
        except ValueError:
            return None
    if isinstance(v, dict):
        norm: Dict[str, Any] = {}
        for k in ("limit", "interval", "max_interval", "type"):
            if k in v:
                norm[k] = v[k]
        # legacy alias
        if "retries" in v and "limit" not in norm:
            norm["limit"] = v["retries"]
        return norm or None
    return None


def retry_tooltip(rt: Dict[str, Any]) -> str:
    """
    Make a compact one-line summary suitable for a node tooltip.
    Examples:
      - "Retry: 3"
      - "Retry: 5 (fixed 30s)"
      - "Retry: 5 (exp 30s..5m)"
    """
    if not rt:
        return ""
    parts = []
    limit = rt.get("limit")
    if limit is not None:
        parts.append(str(limit))
    t = rt.get("type")
    intr = rt.get("interval")
    max_intr = rt.get("max_interval")
    if t or intr or max_intr:
        inner = []
        if t:
            inner.append("exp" if t.startswith("exp") else t)
        if intr:
            inner.append(str(intr))
        if max_intr:
            inner.append(f"..{max_intr}")
        parts.append(f"({' '.join(inner)})")
    return f"Retry: {' '.join(parts)}".strip()
