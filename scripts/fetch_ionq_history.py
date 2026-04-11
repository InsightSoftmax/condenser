"""
Fetch historical IonQ benchmark runs from the IonQ REST API and append to data/ionq/results.csv.

These runs were submitted directly via IonQ (not AWS Braket) from Claire's personal workspace
on qpu.forte-1. Date range: 2025-02-03 to 2025-06-11.

API structure:
  - Parent batch jobs (10 circuits each) are listed via GET /v0.3/jobs
  - Results are at /v0.3/jobs/{parent_id}/results, keyed by child job ID
  - Each child job has gate_counts (1q = X gates, 2q = CNOT gates)
  - Circuit identity is inferred from gate_counts + dominant result
  - Bit ordering: LSB (qubit 0 = bit 0, so key "2" = binary "10" reversed = our "01")

Usage:
    IONQ_API_KEY=... uv run python scripts/fetch_ionq_history.py [--explore] [--dry-run]

Options:
    --explore    Print raw data for the first matching parent job, then exit.
    --dry-run    Show what rows would be written without modifying the CSV.
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.circuits import REFERENCE_TABLE

IONQ_BASE = "https://api.ionq.co/v0.3"
TARGET = "qpu.forte-1"
PLATFORM = "ionq"
BACKEND = "Forte-1"

FIELDNAMES = [
    "run_date", "platform", "backend", "input_bits", "circuit_length",
    "shots", "counts_json", "success_probability", "job_id",
    "job_start_time", "job_end_time", "sdk_version", "notes",
]


def _api_get(key: str, path: str, params: dict | None = None) -> dict | list:
    resp = requests.get(
        f"{IONQ_BASE}{path}",
        headers={"Authorization": f"apiKey {key}"},
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def _ts_to_iso(unix_ts: int | float | None) -> str:
    if not unix_ts:
        return ""
    return datetime.fromtimestamp(unix_ts, tz=timezone.utc).isoformat()


def _ts_to_date(unix_ts: int | float | None) -> str:
    if not unix_ts:
        return ""
    return datetime.fromtimestamp(unix_ts, tz=timezone.utc).date().isoformat()


def _lsb_key_to_bits(key: str, n_qubits: int = 2) -> str:
    """
    Convert an IonQ result key (decimal integer string) to our bitstring notation.
    IonQ uses LSB convention: qubit i is bit i of the integer.
    Our notation: leftmost char = qubit 0.
    So we reverse the binary string: format(k, '02b')[::-1]

    Examples (2 qubits):
        "0" -> "00", "1" -> "10", "2" -> "01", "3" -> "11"
    """
    return format(int(key), f"0{n_qubits}b")[::-1]


def _infer_circuit(n_x_gates: int, circuit_length: int, results: dict) -> tuple[str, int] | None:
    """
    Infer (input_bits, circuit_length) from gate counts and results.

    For n_x=0 or n_x=2: input_bits is unambiguous.
    For n_x=1: use the dominant result to disambiguate "01" vs "10".
    Returns None if inference fails.
    """
    if circuit_length < 1 or circuit_length > 6:
        return None

    dominant_key = max(results, key=lambda k: results[k])
    dominant_bits = _lsb_key_to_bits(dominant_key)

    if n_x_gates == 0:
        return ("00", circuit_length)
    elif n_x_gates == 2:
        return ("11", circuit_length)
    elif n_x_gates == 1:
        for candidate in ("01", "10"):
            expected = REFERENCE_TABLE.get((candidate, circuit_length))
            if expected == dominant_bits:
                return (candidate, circuit_length)
        return None  # ambiguous (shouldn't happen with clean data)
    else:
        return None  # unexpected gate count


def _results_to_counts(results: dict, shots: int) -> dict[str, int]:
    """Convert IonQ result probabilities to shot counts keyed by our bitstring notation."""
    counts: dict[str, int] = {}
    for k, prob in results.items():
        bitstring = _lsb_key_to_bits(k)
        count = round(prob * shots)
        if count > 0:
            counts[bitstring] = count
    return counts


def _fetch_all_forte_parents(key: str) -> list[dict]:
    """Fetch all completed qpu.forte-1 parent batch jobs."""
    all_jobs: list[dict] = []
    params: dict = {"limit": 200}

    while True:
        data = _api_get(key, "/jobs", params=params)
        if isinstance(data, list):
            page_jobs = data
            has_next = False
        else:
            page_jobs = data.get("jobs", [])
            next_cursor = data.get("next")
            has_next = bool(next_cursor)
            if has_next:
                params = {"next": next_cursor}

        all_jobs.extend(page_jobs)
        if not has_next:
            break

    return [
        j for j in all_jobs
        if j.get("target") == TARGET and j.get("status") == "completed"
    ]


def _load_existing_job_ids(csv_path: Path) -> set[str]:
    if not csv_path.exists():
        return set()
    with csv_path.open(newline="") as f:
        return {row["job_id"] for row in csv.DictReader(f)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--explore", action="store_true",
                        help="Print raw data for the first matching parent job, then exit")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be written without modifying the CSV")
    args = parser.parse_args()

    key = os.environ.get("IONQ_API_KEY")
    if not key:
        print("Error: IONQ_API_KEY environment variable is not set", file=sys.stderr)
        sys.exit(1)

    print("Fetching completed qpu.forte-1 jobs...")
    parents = _fetch_all_forte_parents(key)
    print(f"  Found {len(parents)} parent batch jobs on {TARGET}")

    if not parents:
        print("Nothing to do.")
        return

    if args.explore:
        parent = parents[0]
        print(f"\n--- Parent job (raw) ---")
        print(json.dumps(parent, indent=2))
        try:
            results = _api_get(key, f"/jobs/{parent['id']}/results")
            print(f"\n--- Results (keyed by child ID) ---")
            print(json.dumps(results, indent=2))
            full = _api_get(key, f"/jobs/{parent['id']}")
            children = full.get("children", [])
            if children:
                print(f"\n--- First child job ---")
                child = _api_get(key, f"/jobs/{children[0]}")
                print(json.dumps(child, indent=2))
        except Exception as e:
            print(f"Error fetching details: {e}")
        return

    csv_path = Path("data/ionq/results.csv")
    existing_ids = _load_existing_job_ids(csv_path)
    print(f"  Existing job IDs in CSV: {len(existing_ids)}")

    rows: list[dict] = []
    skipped_no_children = 0
    skipped_parse = 0
    skipped_null_results = 0  # circuits reserved but not executed (execution_time=0)
    skipped_dup = 0

    for i, parent in enumerate(parents):
        parent_id = parent["id"]
        run_date = _ts_to_date(parent.get("request"))
        shots = parent.get("shots", 100)

        print(f"  [{i+1}/{len(parents)}] {run_date} {parent_id[:8]}...", end=" ", flush=True)

        # Fetch results (keyed by child ID → {decimal_key: probability})
        try:
            results_by_child = _api_get(key, f"/jobs/{parent_id}/results")
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                print("results expired, skipping")
                skipped_null_results += 1
                continue
            raise
        time.sleep(0.1)

        if not isinstance(results_by_child, dict) or "error" in results_by_child:
            print("no results")
            skipped_null_results += 1
            continue

        # Fetch full parent to get children list
        full_parent = _api_get(key, f"/jobs/{parent_id}")
        children = full_parent.get("children", [])
        time.sleep(0.1)

        if not children:
            print("no children")
            skipped_no_children += 1
            continue

        batch_rows = 0
        for child_id in children:
            if child_id in existing_ids:
                skipped_dup += 1
                continue

            child_results = results_by_child.get(child_id)
            if not child_results:
                # null result = circuit was reserved but never executed (execution_time=0)
                skipped_null_results += 1
                continue

            # Fetch child to get gate_counts
            try:
                child_job = _api_get(key, f"/jobs/{child_id}")
            except Exception:
                skipped_parse += 1
                continue
            time.sleep(0.05)

            gc = child_job.get("gate_counts", {})
            n_x = gc.get("1q", 0)
            circuit_length = gc.get("2q", 0)

            parsed = _infer_circuit(n_x, circuit_length, child_results)
            if parsed is None:
                skipped_parse += 1
                continue

            input_bits, circuit_length = parsed
            counts = _results_to_counts(child_results, shots)
            correct = REFERENCE_TABLE[(input_bits, circuit_length)]
            success_prob = counts.get(correct, 0) / shots if shots else 0.0

            rows.append({
                "run_date": run_date,
                "platform": PLATFORM,
                "backend": BACKEND,
                "input_bits": input_bits,
                "circuit_length": circuit_length,
                "shots": shots,
                "counts_json": json.dumps(counts),
                "success_probability": round(success_prob, 4),
                "job_id": child_id,
                "job_start_time": _ts_to_iso(child_job.get("start")),
                "job_end_time": _ts_to_iso(child_job.get("response")),
                "sdk_version": "",
                "notes": "fetched_from_ionq_api",
            })
            batch_rows += 1

        print(f"{batch_rows} circuits")

    print(f"\nTotal: {len(rows)} new rows | {skipped_dup} duplicates | "
          f"{skipped_null_results} null/expired results | {skipped_parse} parse failures | "
          f"{skipped_no_children} no children")

    if not rows:
        print("Nothing to write.")
        return

    rows.sort(key=lambda r: (r["run_date"], r["job_id"]))

    if args.dry_run:
        print(f"\n--- Dry run: first 3 of {len(rows)} rows ---")
        for row in rows[:3]:
            print(json.dumps(row, indent=2))
        print(f"\nWould append {len(rows)} rows to {csv_path}")
        return

    write_header = not csv_path.exists()
    with csv_path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in FIELDNAMES})

    print(f"Wrote {len(rows)} rows to {csv_path}")


if __name__ == "__main__":
    main()
