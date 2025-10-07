
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
import yaml
from .logging_config import get_logger

logger = get_logger(__name__)

class DigLoader(yaml.FullLoader):
    def __init__(self, stream):
        self._root = Path(getattr(stream, "name", ".")).resolve().parent
        super().__init__(stream)

@dataclass(frozen=True)
class IncludeRef:
    path: str
    base: Path

def _construct_include(loader: DigLoader, node: yaml.nodes.ScalarNode) -> "IncludeRef":
    rel = loader.construct_scalar(node)
    return IncludeRef(rel, loader._root)

yaml.add_constructor("!include", _construct_include, Loader=DigLoader)
# Some YAML writers tokenize the key as a tag named "!include:" (including the colon).
# Register both to be robust across environments.
yaml.add_constructor("!include:", _construct_include, Loader=DigLoader)

def _deep_merge(dst: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in src.items():
        if k in dst and isinstance(dst[k], dict) and isinstance(v, dict):
            _deep_merge(dst[k], v)
        else:
            dst[k] = v
    return dst

def resolve_includes(obj: Any) -> Any:
    if isinstance(obj, IncludeRef):
        inc_path = (obj.base / obj.path).resolve()
        try:
            with open(inc_path, "r", encoding="utf-8") as f:
                loaded = yaml.load(f, Loader=DigLoader)
            return resolve_includes(loaded)
        except FileNotFoundError:
            logger.warning(f"Include file not found: {inc_path}")
            return {}

    if isinstance(obj, dict):
        resolved = {}
        for k, v in obj.items():
            if isinstance(k, IncludeRef):
                continue
            resolved[k] = resolve_includes(v)

        for k, v in obj.items():
            if not isinstance(k, IncludeRef):
                continue
            paths = []
            if k.path:
                paths = [k.path]
            else:
                if isinstance(v, str):
                    paths = [v]
                elif isinstance(v, (list, tuple)):
                    paths = list(v)
                else:
                    continue
            for rel in paths:
                inc_abs = (k.base / rel).resolve()
                try:
                    with open(inc_abs, "r", encoding="utf-8") as f:
                        inc_loaded = yaml.load(f, Loader=DigLoader)
                    inc_resolved = resolve_includes(inc_loaded)
                    if isinstance(inc_resolved, dict):
                        _deep_merge(resolved, inc_resolved)
                    else:
                        resolved.setdefault("_included_values", []).append(inc_resolved)
                except FileNotFoundError:
                    logger.warning(f"Include file not found: {inc_abs}")
        return resolved

    if isinstance(obj, list):
        return [resolve_includes(v) for v in obj]
    return obj
