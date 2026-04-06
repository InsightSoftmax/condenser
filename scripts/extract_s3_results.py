"""
Extract and convert Braket task results from S3 into per-platform CSVs.

Designed to run in AWS CloudShell where credentials are already available.

Usage:
    python3 extract_s3_results.py

Outputs: rigetti_results.csv, ionq_results.csv (and any other platforms found)
Then download via CloudShell Actions → Download file.
"""

import csv
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

BUCKET = "amazon-braket-eng-dev"
PREFIX = "yuval_mwe_preliminary"
LOCAL_DIR = Path(__file__).parent.parent / "data" / "braket-raw"

REFERENCE_TABLE = {
    ("00", 1): "00", ("00", 2): "00", ("00", 3): "00",
    ("00", 4): "00", ("00", 5): "00", ("00", 6): "00",
    ("01", 1): "01", ("01", 2): "11", ("01", 3): "10",
    ("01", 4): "10", ("01", 5): "11", ("01", 6): "01",
    ("10", 1): "11", ("10", 2): "01", ("10", 3): "01",
    ("10", 4): "11", ("10", 5): "10", ("10", 6): "10",
    ("11", 1): "10", ("11", 2): "10", ("11", 3): "11",
    ("11", 4): "01", ("11", 5): "01", ("11", 6): "11",
}

FIELDNAMES = [
    "run_date", "platform", "backend", "input_bits", "circuit_length",
    "shots", "counts_json", "success_probability", "job_id",
    "job_start_time", "job_end_time", "sdk_version", "notes",
]


def parse_circuit(source: str) -> tuple[str, int]:
    """Reconstruct input_bits and circuit_length from OpenQASM source."""
    bit0 = "1" if "x q[0]" in source else "0"
    bit1 = "1" if "x q[1]" in source else "0"
    circuit_length = source.count("cnot")
    return bit0 + bit1, circuit_length


def measurements_to_counts(measurements: list) -> dict:
    """Convert raw shot arrays [[q0,q1], ...] to bitstring histogram."""
    counts: dict[str, int] = defaultdict(int)
    for shot in measurements:
        counts["".join(str(b) for b in shot)] += 1
    return dict(counts)


def platform_from_device(device_id: str) -> str:
    lower = device_id.lower()
    if "rigetti" in lower:
        return "rigetti"
    if "ionq" in lower:
        return "ionq"
    return "unknown"


def probs_to_counts(probs: dict, shots: int) -> dict:
    """Convert IonQ-style probability dict to integer counts."""
    return {bs: round(p * shots) for bs, p in probs.items()}


def process_result(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text())
        source = data["additionalMetadata"]["action"]["source"]
        input_bits, circuit_length = parse_circuit(source)

        if circuit_length == 0 or circuit_length > 6:
            return None

        meta = data["taskMetadata"]
        shots = meta.get("shots", 0)

        if data.get("measurements") is not None:
            counts = measurements_to_counts(data["measurements"])
            shots = len(data["measurements"])
        elif data.get("measurementProbabilities") is not None:
            counts = probs_to_counts(data["measurementProbabilities"], shots)
        else:
            return None

        device_id = meta["deviceId"]
        platform = platform_from_device(device_id)
        backend = device_id.split("/")[-1]

        created_at = meta.get("createdAt", "")
        ended_at = meta.get("endedAt", "")
        run_date = created_at[:10] if created_at else ""

        correct = REFERENCE_TABLE.get((input_bits, circuit_length))
        if correct is None:
            return None

        success_prob = counts.get(correct, 0) / shots if shots > 0 else 0.0

        return {
            "run_date": run_date,
            "platform": platform,
            "backend": backend,
            "input_bits": input_bits,
            "circuit_length": circuit_length,
            "shots": shots,
            "counts_json": json.dumps(counts),
            "success_probability": round(success_prob, 4),
            "job_id": meta.get("id", ""),
            "job_start_time": created_at,
            "job_end_time": ended_at,
            "sdk_version": "",
            "notes": "",
        }
    except Exception:
        return None


def sync_from_s3() -> None:
    LOCAL_DIR.mkdir(exist_ok=True)
    print(f"Syncing results.json files from s3://{BUCKET}/{PREFIX}/ ...")
    result = subprocess.run([
        "aws", "s3", "sync",
        f"s3://{BUCKET}/{PREFIX}/",
        str(LOCAL_DIR),
        "--exclude", "*",
        "--include", "*/results.json",
    ])
    if result.returncode != 0:
        print("S3 sync failed.", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    if not LOCAL_DIR.exists():
        sync_from_s3()
    else:
        print(f"Using existing local data at {LOCAL_DIR}")

    result_files = sorted(LOCAL_DIR.glob("*/results.json"))
    total = len(result_files)
    print(f"\nProcessing {total} result files...")

    rows_by_platform: dict[str, list[dict]] = defaultdict(list)
    skipped = 0

    for i, path in enumerate(result_files):
        if i % 500 == 0:
            print(f"  {i}/{total}...")
        row = process_result(path)
        if row and row["platform"] != "unknown":
            rows_by_platform[row["platform"]].append(row)
        else:
            skipped += 1

    print(f"Done. Skipped {skipped} unrecognised/malformed/simulator results.\n")

    data_dir = Path(__file__).parent.parent / "data"
    for platform, rows in sorted(rows_by_platform.items()):
        rows.sort(key=lambda r: (r["run_date"], r["job_id"]))
        out = data_dir / platform / "results.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)

        dates = sorted({r["run_date"] for r in rows})
        avg_success = sum(r["success_probability"] for r in rows) / len(rows)
        print(f"{platform}: {len(rows)} tasks | {len(dates)} dates "
              f"| {dates[0]} → {dates[-1]} | avg success {avg_success:.3f}")
        print(f"  → {out}")


if __name__ == "__main__":
    main()
