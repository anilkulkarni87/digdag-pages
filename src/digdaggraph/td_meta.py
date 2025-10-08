from __future__ import annotations

import os
import re
from typing import Any, Dict, Optional

TD_CONSOLE_BASE = os.getenv("TD_CONSOLE_BASE", "https://console.treasuredata.com").rstrip("/")


def _looks_nonempty(v: Any) -> bool:
    return v is not None and v != ""


def td_task_meta(task_val: Any, exports: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract Treasure Data meta for a td> task.
    Prefers task-specific values over _export.
    Also recognizes Digdag `_retry`.
    """
    task = task_val if isinstance(task_val, dict) else {}
    exp = exports if isinstance(exports, dict) else {}

    def pick(*keys: str) -> Optional[str]:
        for key in keys:
            v = task.get(key)
            if _looks_nonempty(v):
                return v
            v = exp.get(key)
            if _looks_nonempty(v):
                return v
        return None

    meta = {
        "database": pick("database"),
        "engine": pick("engine"),  # presto|hive|spark
        "priority": pick("priority"),
        "retry": pick("_retry", "retry", "retries"),  # <-- include _retry
        "timezone": pick("timezone"),
        "result_connection": pick("result_connection"),
        "result_settings": pick("result_settings"),
    }
    return {k: v for k, v in meta.items() if v is not None}


_TABLE_RE = re.compile(r"\bfrom\s+([a-zA-Z0-9_\.]+)", re.IGNORECASE)


def guess_table(sql_text: str) -> Optional[str]:
    if not isinstance(sql_text, str):
        return None
    m = _TABLE_RE.search(sql_text)
    return m.group(1) if m else None


def td_console_links(meta: Dict[str, Any], sql_text: Optional[str]) -> Dict[str, str]:
    links: Dict[str, str] = {}
    base = TD_CONSOLE_BASE

    db = meta.get("database")
    eng = meta.get("engine")

    if db:
        links["Open database"] = f"{base}/app/databases/{db}"
        params = [f"database={db}"]
        if eng:
            params.append(f"engine={eng}")
        q = "&".join(params)
        links["Open in query editor"] = f"{base}/app/new_query?{q}"
        table = guess_table(sql_text or "")
        if table:
            if "." in table:
                db2, tbl = table.split(".", 1)
            else:
                db2, tbl = db, table
            links["Open table"] = f"{base}/app/databases/{db2}/tables/{tbl}"
    return links


def td_tooltip(meta: Dict[str, Any]) -> str:
    bits = []
    if "database" in meta:
        bits.append(f"DB: {meta['database']}")
    if "engine" in meta:
        bits.append(f"Engine: {meta['engine']}")
    if "priority" in meta:
        bits.append(f"Priority: {meta['priority']}")
    if "retry" in meta and meta["retry"] not in ("", None):
        bits.append(f"Retry: {meta['retry']}")
    if "timezone" in meta:
        bits.append(f"TZ: {meta['timezone']}")
    if "result_connection" in meta:
        bits.append(f"Result: {meta['result_connection']}")
    return " • ".join(bits) if bits else "Treasure Data task"
