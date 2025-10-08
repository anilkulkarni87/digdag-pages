from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from graphviz import Digraph
from cron_descriptor import get_description

from .graph_blocks import Block
from .yaml_includes import DigLoader, resolve_includes
from .sql_extract import maybe_sql_path
from .html_pages import write_workflow_html_inline, write_sql_page
from .index_page import ScheduleEntry
from .constants import GRAPHS_DIR
from .logging_config import get_logger
from .td_meta import td_task_meta, td_console_links, td_tooltip  # NEW
from .digdag_meta import normalize_retry, retry_tooltip


logger = get_logger(__name__)


# -------- Operator palette (shapes/colors) ----------
# Extend here as you add awareness for more operators.
PALETTE = {
    "td>": dict(color="webgreen", shape="box"),
    "td_load>": dict(color="darkseagreen4", shape="cds"),
    "td_wait>": dict(color="darkgoldenrod3", shape="hexagon"),
    "td_for_each>": dict(color="lightskyblue4", shape="folder"),
    "http>": dict(color="darkgreen", shape="box"),
    "mail>": dict(color="crimson", shape="box"),
    "if>": dict(color="darkorchid2", shape="diamond"),
    "call>": dict(color="cornflowerblue", shape="box"),
    "require>": dict(color="cornflowerblue", shape="box"),
    "_do": dict(color="green", shape="note"),
    "_error": dict(color="red", shape="Mcircle"),
}


def _style_for(key: str) -> Dict[str, str]:
    # Normalize e.g., "td>" or "td_load>" etc.; default style if unknown
    return PALETTE.get(key, {"color": "lightslategrey", "shape": "box"})


def _proj_from_path(filepath: str) -> str:
    return Path(filepath).parent.name


def _wf_from_path(filepath: str) -> str:
    return Path(filepath).name


def _workflow_html_abs(filepath: str) -> Path:
    project = _proj_from_path(filepath)
    wf_html = _wf_from_path(filepath).replace(".dig", ".html")
    return Path(os.getcwd()) / GRAPHS_DIR / project / wf_html


def _workflow_html_href(filepath: str) -> str:
    project = _proj_from_path(filepath)
    wf_html = _wf_from_path(filepath).replace(".dig", ".html")
    return f"./{GRAPHS_DIR}/{project}/{wf_html}"


def _kv_lines(d: Dict[str, Any], prefix: str = "") -> List[str]:
    lines: List[str] = []
    for k, v in d.items():
        if isinstance(v, dict):
            lines.append(f"{prefix}{k}:")
            lines.extend(_kv_lines(v, prefix + "  "))
        else:
            lines.append(f"{prefix}{k}: {v}")
    return lines


def _load_block_tree(
    root: Block,
    data: Optional[Dict[str, Any]],
    filepath: str,
    schedule_entries: List[ScheduleEntry],
) -> None:
    root.penwidth = 1.0
    root.URL = ""
    dirpath = str(Path(filepath).parent) + "/"

    if data is None:
        data = {"Empty Task": "This is empty dummy task"}

    # Prefer reading global exports once for td meta
    global_exports = data.get("_export", {}) if isinstance(data, dict) else {}

    for key in list(data.keys()):
        val = data.get(key)
        logger.info(f"{key} --> {val}")

        project = _proj_from_path(filepath)
        workflow_name = _wf_from_path(filepath)

        if key == "timezone":
            st = _style_for("timezone")
            root.append(val, color="mediumspringgreen", shape="cds")

        if key == "schedule":
            if isinstance(val, dict) and "cron>" in val:
                label = f"{json.dumps(val)}\n{get_description(val['cron>'])}"
            else:
                label = f"{key}\n{json.dumps(val)}"
            st = _style_for("schedule")
            root.append(label=label, color="magenta1", URL="", shape="component")
            schedule_entries.append(
                ScheduleEntry(
                    project=project,
                    workflow=workflow_name,
                    schedule_text=label,
                    href=_workflow_html_href(filepath),
                )
            )

        if key == "_export":
            label = f"_export\n{chr(10).join(_kv_lines(val))}"
            st = _style_for("_export")
            root.append(label=label, color="goldenrod4", URL="", shape="box3d", penwidth=2.0)

        if key == "_parallel":
            root.color = "purple2"
            root.parallel = val

        # ---- TD operator awareness ----
        if key in ("td>", "td_load>", "td_wait>", "td_for_each>"):
            st = _style_for(key)
            root.color = st["color"]
            root.shape = st["shape"]
            root.penwidth = 1.5
            root.label = f"{root.label}\n{val}"

            # TD meta + tooltip
            meta = td_task_meta(val, global_exports)
            root.tooltip = td_tooltip(meta)

            # If it's a td> query (not load/wait/for_each) and references SQL, generate a page + link
            if key == "td>":
                sql_path = maybe_sql_path(val)
                if sql_path:
                    workflow_html_abs = _workflow_html_abs(filepath)
                    src_sql_abs = Path(filepath).parent / sql_path  # read relative to .dig
                    logger.info(f"Reading SQL from {src_sql_abs}")

                    # Output under graphs/<project>/queries/... .html
                    out_html_abs = (
                        Path(os.getcwd()) / GRAPHS_DIR / project / Path(sql_path).with_suffix(".html")
                    )
                    out_html_abs.parent.mkdir(parents=True, exist_ok=True)

                    try:
                        sql_text = src_sql_abs.read_text(encoding="utf-8")
                    except FileNotFoundError:
                        sql_text = f"-- FileNotFoundError: {src_sql_abs}"
                        logger.warning(f"SQL file not found: {src_sql_abs}")

                    # TD Console links
                    links = td_console_links(meta, sql_text)

                    # Back link + write SQL page (now with meta & links)
                    back_href = os.path.relpath(workflow_html_abs, out_html_abs.parent).replace(
                        "\\", "/"
                    )
                    write_sql_page(
                        project=project,
                        querypath=sql_path,
                        sql_text=sql_text,
                        back_href=back_href,
                        out_html_abs=out_html_abs,
                        td_meta=meta,
                        td_links=links,
                    )

                    # Link the graph node to the generated SQL page
                    href_from_workflow = os.path.relpath(
                        out_html_abs, workflow_html_abs.parent
                    ).replace("\\", "/")
                    root.URL = href_from_workflow

        # Other ops (http/mail/if/call/require)
        if key == "http>":
            st = _style_for("http>")
            root.color = st["color"]
            root.shape = st["shape"]
            root.label = f"{root.label}\n{val}"

        if key == "mail>":
            st = _style_for("mail>")
            root.color = st["color"]
            root.shape = st["shape"]
            root.label = f"{root.label}\n{val}"

        if key == "if>":
            st = _style_for("if>")
            root.color = st["color"]
            root.shape = st["shape"]
            root.label = f"{root.label}\nif {val}"

        if key in ("call>", "require>"):
            st = _style_for(key)
            fpath = dirpath + val
            root.color = st["color"]
            root.shape = st["shape"]
            root.penwidth = 3.0
            if not fpath.endswith(".dig"):
                fpath += ".dig"
                root.label = f"{root.label}\n{val}.dig"
                root.URL = f"./{val}.html"
            if not os.path.exists(fpath):
                for p in Path(fpath).parent.parent.rglob(f"{val}.dig"):
                    root.URL = f"../{p.parent.name}/{val}.html"

        if key in ["_do"]:
            st = _style_for("_do")
            block = root.append(key, penwidth=1.0, color=st["color"], shape=st["shape"])
            _load_block_tree(block, val, filepath, schedule_entries)

        if key in ["_error"]:
            st = _style_for("_error")
            block = root.append(key, penwidth=1.0, color=st["color"], shape=st["shape"])
            _load_block_tree(block, val, filepath, schedule_entries)
        
                # --- Digdag retry annotation ---
        if key == "_retry":
            rt = normalize_retry(val)
            if rt:
                # Append a line to the node label for quick visibility
                root.label = f"{root.label}\n_retry: {rt.get('limit', val)}"
                # Enrich tooltip (append; keep existing content)
                tip = retry_tooltip(rt)
                if tip:
                    root.tooltip = (root.tooltip + " • " + tip) if root.tooltip else tip


        # Only process tasks starting with '+'
        if not key.startswith("+"):
            continue

        if root.label == "Click to HomePage":
            from .constants import SCHEDULE_INDEX_FILE

            root.URL = f"../../{SCHEDULE_INDEX_FILE}"

        child = root.append(key)
        _load_block_tree(child, val, filepath, schedule_entries)


def generate_graph(input_filepath: str, output_dot_file: str) -> None:
    """
    Build the graph for a single .dig file, render SVG + inline-HTML page,
    and generate SQL pages for any td> file references.
    """
    dot = Digraph(format="svg", edge_attr={"color": "red"})
    dot.attr(target="_top")
    root = Block("root", "Click to HomePage", "brown")

    try:
        with open(input_filepath, encoding="utf-8") as f:
            import yaml

            data_raw = yaml.load(f, Loader=DigLoader)
            data = resolve_includes(data_raw)
            _load_block_tree(root, data, input_filepath, [])
    except FileNotFoundError:
        logger.error(f"Input file not found: {input_filepath}")
        return
    except Exception as e:
        logger.error(f"Error loading workflow {input_filepath}: {e}", exc_info=True)
        return

    root.draw(dot)

    try:
        dot.render(output_dot_file)
    except Exception as e:
        logger.error(f"Error rendering graph for {input_filepath}: {e}", exc_info=True)
        return

    svg_path = output_dot_file + ".svg"
    try:
        svg_text = Path(svg_path).read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed reading SVG {svg_path}: {e}")
        svg_text = (
            "<svg xmlns='http://www.w3.org/2000/svg'><text x='10' y='20'>SVG read error</text></svg>"
        )

    html_path = output_dot_file + ".html"
    project = _proj_from_path(input_filepath)
    workflow = _wf_from_path(input_filepath)
    write_workflow_html_inline(svg_text, html_path, project, workflow)
