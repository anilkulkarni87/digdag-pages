import time
from pathlib import Path
import os
from .constants import GRAPHS_DIR, SCHEDULE_INDEX_FILE, UNSCHEDULED_INDEX_FILE
from .graph_generate import generate_graph
from .index_page import write_scheduled_workflows, ScheduleEntry, write_unscheduled_workflows
from .logging_config import get_logger

logger = get_logger(__name__)


def _label_for_schedule(schedule_obj) -> str:
    """
    Build a robust label for the schedule table row.
    Prefer cron humanization when possible, but never fail the row.
    """
    try:
        import yaml
        label_core = yaml.safe_dump(schedule_obj).strip()
    except Exception:
        import json

        label_core = f"{schedule_obj!r}" if isinstance(schedule_obj, str) else json.dumps(schedule_obj)

    # Try to humanize cron, but never make this fatal
    try:
        if isinstance(schedule_obj, dict) and "cron>" in schedule_obj:
            from cron_descriptor import get_description

            return f"{label_core}\n{get_description(schedule_obj['cron>'])}"
    except Exception as e:
        logger.warning(f"cron description failed: {e}")

    return f"schedule\n{label_core}"


def main() -> None:
    start_time = time.time()
    count = 0
    Path(GRAPHS_DIR).mkdir(exist_ok=True)
    schedule_entries: list[ScheduleEntry] = []
    unscheduled_entries: list[ScheduleEntry] = []  

    # Discover .dig files
    dig_files = [p for p in Path(os.getcwd()).rglob("*.dig") if GRAPHS_DIR not in str(p)]
    logger.info(f"Found {len(dig_files)} .dig files")

    for path in dig_files:
        input_file_path = path
        out_dir = Path(os.getcwd()) / GRAPHS_DIR / path.parent.name
        out_dir.mkdir(parents=True, exist_ok=True)
        output_dot_file = str(out_dir / path.name.replace(".dig", ""))
        logger.info(f"BEGIN generating graph for {input_file_path}")
        print(f"Generating graph for {input_file_path} → {output_dot_file}")
        try:
            generate_graph(input_filepath=str(input_file_path), output_dot_file=output_dot_file)
            count += 1
            logger.info(f"COMPLETE generating graph for {input_file_path}")
        except Exception as e:
            logger.error(f"FAILED generating graph for {input_file_path}: {e}", exc_info=True)
            # continue on other files
            continue

        # Collect schedule entry (robust, never fatal)
        try:
            import yaml
            from .yaml_includes import DigLoader, resolve_includes

            with open(input_file_path, encoding="utf-8") as f:
                data_raw = yaml.load(f, Loader=DigLoader)
                data = resolve_includes(data_raw) or {}
            if "schedule" in data:
                label = _label_for_schedule(data["schedule"])
                schedule_entries.append(
                    ScheduleEntry(
                        project=path.parent.name,
                        workflow=path.name,
                        schedule_text=label,
                        href=f"./{GRAPHS_DIR}/{path.parent.name}/{path.name.replace('.dig','.html')}",
                    )
                )
            else:
                # NEW: track unscheduled
                unscheduled_entries.append(
                    ScheduleEntry(
                        project=path.parent.name,
                        workflow=path.name,
                        schedule_text="",   # ignored by the unscheduled page
                        href=href,
                    )
                )
        except Exception as e:
            logger.warning(f"Schedule collection failed for {input_file_path}: {e}")

    # Always write the index
    write_scheduled_workflows(schedule_entries, out_path=SCHEDULE_INDEX_FILE)
    write_unscheduled_workflows(unscheduled_entries, out_path=UNSCHEDULED_INDEX_FILE)

    elapsed = time.time() - start_time
    print(f"Graphs generated: {count} | TIME: {elapsed:.2f}s")
    print(f"Workflows: {len(dig_files)} | scheduled: {len(schedule_entries)} | unscheduled: {len(unscheduled_entries)}")
    print(f"Wrote {SCHEDULE_INDEX_FILE} and {UNSCHEDULED_INDEX_FILE}")


if __name__ == "__main__":
    main()
