import time
from pathlib import Path
import os
from .constants import GRAPHS_DIR, SCHEDULE_INDEX_FILE
from .graph_generate import generate_graph
from .index_page import write_scheduled_workflows, ScheduleEntry
from .logging_config import get_logger

logger = get_logger(__name__)


def main() -> None:
    start_time = time.time()
    count = 0
    Path(GRAPHS_DIR).mkdir(exist_ok=True)
    schedule_entries: list[ScheduleEntry] = []

    for path in Path(os.getcwd()).rglob("*.dig"):
        if GRAPHS_DIR in str(path):
            continue
        input_file_path = path
        out_dir = Path(os.getcwd()) / GRAPHS_DIR / path.parent.name
        out_dir.mkdir(parents=True, exist_ok=True)
        output_dot_file = str(out_dir / path.name.replace(".dig", ""))
        logger.info(f"BEGIN generating graph for {input_file_path}")
        print(f"Generating graph for {input_file_path} → {output_dot_file}")
        try:
            generate_graph(input_filepath=str(input_file_path), output_dot_file=output_dot_file)
            # collect schedule entries (best-effort lightweight parse)
            try:
                import yaml
                import json
                from cron_descriptor import get_description
                from .yaml_includes import DigLoader, resolve_includes

                with open(input_file_path, encoding="utf-8") as f:
                    data_raw = yaml.load(f, Loader=DigLoader)
                    data = resolve_includes(data_raw) or {}
                    if "schedule" in data:
                        if isinstance(data["schedule"], dict) and "cron>" in data["schedule"]:
                            label = (
                                f"{yaml.safe_dump(data['schedule']).strip()}"
                                f"\n{get_description(data['schedule']['cron>'])}"
                            )
                        else:
                            label = f"schedule\n{json.dumps(data['schedule'])}"
                        schedule_entries.append(
                            ScheduleEntry(
                                project=path.parent.name,
                                workflow=path.name,
                                schedule_text=label,
                                href=f"./{GRAPHS_DIR}/{path.parent.name}/{path.name.replace('.dig','.html')}",
                            )
                        )
            except Exception:
                # don't let schedule parsing failures break the whole run
                pass
            count += 1
            logger.info(f"COMPLETE generating graph for {input_file_path}")
        except Exception as e:
            logger.error(f"FAILED generating graph for {input_file_path}: {e}", exc_info=True)

    # Always write the index, even if there were zero .dig files
    write_scheduled_workflows(schedule_entries, out_path=SCHEDULE_INDEX_FILE)

    elapsed = time.time() - start_time
    print(f"Graphs generated: {count} | TIME: {elapsed:.2f}s")
    print(f"Wrote {SCHEDULE_INDEX_FILE}")


if __name__ == "__main__":
    main()
