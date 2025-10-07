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

logger = get_logger(__name__)


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

    for key in list(data.keys()):
        logger.info(f"{key} --> {data.get(key)}")

        project = _proj_from_path(filepath)
        workflow_name = _wf_from_path(filepath)

        if key == "timezone":
            root.append(data[key], color="mediumspringgreen", shape="cds")

        if key == "schedule":
            if isinstance(data[key], dict) and "cron>" in data[key]:
                label = f"{json.dumps(data[key])}\n{get_description(data[key]['cron>'])}"
            else:
                label = f"{key}\n{json.dumps(data[key])}"
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
            label = f"_export\n{chr(10).join(_kv_lines(data[key]))}"
            root.append(label=label, color="goldenrod4", URL="", shape="box3d", penwidth=2.0)

        if key == "_parallel":
            root.color = "purple2"
            root.parallel = data[key]

        # td> tasks — generate a SQL page when a file ref is found
        if key == "td>":
            root.color = "webgreen"
            root.label = f"{root.label}\n{data[key]}"
            root.penwidth = 1.5

            sql_path = maybe_sql_path(data[key])
            if sql_path:
                workflow_html_abs = _workflow_html_abs(filepath)

                # ✅ FIX: resolve SQL source relative to the .dig directory
                src_sql_abs = Path(filepath).parent / sql_path
                logger.info(f"Reading SQL from {src_sql_abs}")

                # Output HTML path remains under graphs/<project>/queries/... (preserve nested dirs)
                out_html_abs = (
                    Path(os.getcwd()) / GRAPHS_DIR / project / Path(sql_path).with_suffix(".html")
                )
                out_html_abs.parent.mkdir(parents=True, exist_ok=True)

                try:
                    sql_text = src_sql_abs.read_text(encoding="utf-8")
                except FileNotFoundError:
                    sql_text = f"-- FileNotFoundError: {src_sql_abs}"
                    logger.warning(f"SQL file not found: {src_sql_abs}")

                # Robust back link + write SQL page
                back_href = os.path.relpath(workflow_html_abs, out_html_abs.parent).replace("\\", "/")
                write_sql_page(project, sql_path, sql_text, back_href, out_html_abs)

                # Link the task node to the generated SQL page
                href_from_workflow = os.path.relpath(
                    out_html_abs, workflow_html_abs.parent
                ).replace("\\", "/")
                root.tooltip = "Open SQL"
                root.URL = href_from_workflow
            else:
                root.tooltip = str(data[key])

        if key == "echo>":
            root.color = "lightslategray"
            root.label = f"{root.label}\n{data}"
            root.penwidth = 1.9

        if key == "http>":
            root.color = "darkgreen"
            root.label = f"{root.label}\n{data[key]}"

        if key == "mail>":
            root.color = "crimson"
            root.label = f"{root.label}\n{data[key]}"

        if key == "if>":
            root.color = "darkorchid2"
            root.label = f"{root.label}\nif {data[key]}"
            root.shape = "diamond"

        if key in ("call>", "require>"):
            fpath = dirpath + data[key]
            root.color = "cornflowerblue"
            root.penwidth = 3.0
            if not fpath.endswith(".dig"):
                fpath += ".dig"
                root.label = f"{root.label}\n{data[key]}.dig"
                root.URL = f"./{data[key]}.html"
            # Attempt to find it in sibling projects if not local
            if not os.path.exists(fpath):
                for path in Path(fpath).parent.parent.rglob(f"{data[key]}.dig"):
                    root.URL = f"../{path.parent.name}/{data[key]}.html"

        if key in ["_do"]:
            block = root.append(key, penwidth=1.0, color="green", shape="note")
            _load_block_tree(block, data[key], filepath, schedule_entries)

        if key in ["_error"]:
            block = root.append(key, penwidth=1.0, color="red", shape="Mcircle")
            _load_block_tree(block, data[key], filepath, schedule_entries)

        # Only process tasks starting with '+'
        if not key.startswith("+"):
            continue

        if root.label == "Click to HomePage":
            from .constants import SCHEDULE_INDEX_FILE

            root.URL = f"../../{SCHEDULE_INDEX_FILE}"

        child = root.append(key)
        _load_block_tree(child, data[key], filepath, schedule_entries)


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

    # Write raw SVG + wrapper HTML
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
