"""
Check pending jobs and collect results for any that have completed.

Reads all files under pending/<platform>/*.json.
For each batch where all jobs are done, appends results to data/<platform>/results.csv
and removes the pending file.

Designed to run on a schedule (e.g., every 6 hours) until results arrive,
regardless of how long the queue is.

Usage:
    uv run python scripts/collect_results.py
"""

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

FIELDNAMES = [
    "run_date", "platform", "backend", "input_bits", "circuit_length",
    "shots", "counts_json", "success_probability", "job_id",
    "job_start_time", "job_end_time", "sdk_version", "notes",
]


def append_results(platform: str, results: list[dict]) -> None:
    out_path = Path("data") / platform / "results.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not out_path.exists()
    with out_path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()
        for row in results:
            writer.writerow({k: row.get(k, "") for k in FIELDNAMES})
    print(f"  Wrote {len(results)} rows to {out_path}")


def main() -> None:
    pending_root = Path("pending")
    if not pending_root.exists():
        print("No pending directory found. Nothing to collect.")
        return

    pending_files = sorted(pending_root.glob("*/*.json"))
    if not pending_files:
        print("No pending jobs found.")
        return

    print(f"Found {len(pending_files)} pending batch(es).")
    any_still_waiting = False

    for pending_path in pending_files:
        platform_name = pending_path.parent.name
        print(f"\n=== {platform_name} / {pending_path.name} ===")

        pending = json.loads(pending_path.read_text())

        try:
            module = __import__(f"benchmarks.{platform_name}", fromlist=["collect"])
            results = module.collect(pending)
        except RuntimeError as e:
            # Jobs failed — log and remove the pending file so we don't retry forever
            print(f"  FAILED: {e}")
            pending_path.unlink()
            continue
        except Exception as e:
            print(f"  ERROR: {e}")
            raise

        if results is None:
            print("  Still waiting.")
            any_still_waiting = True
        else:
            append_results(pending["platform"], results)
            pending_path.unlink()
            print(f"  Done. Removed {pending_path}")

    if any_still_waiting:
        print("\nSome batches are still pending. Re-run this script later.")
    else:
        print("\nAll pending batches collected.")


if __name__ == "__main__":
    main()
