"""
One-time script to import Sami's historical IBM Qiskit results into data/ibm/results.csv.

Sami's CSVs contain: index, input_bits, circuit_length, success_probability.
We reconstruct the full schema using filename metadata. Raw shot counts were not
recorded, so counts_json is set to "{}".

Usage:
    uv run python scripts/import_ibm_history.py
"""

import sys
from pathlib import Path

import pandas as pd

ARCHIVE_DIR = Path(__file__).parent.parent / "archive" / "ibm"
OUT_PATH = Path(__file__).parent.parent / "data" / "ibm" / "results.csv"

PLATFORM = "ibm"
BACKEND = "ibm_brisbane"

# filename_key → (run_date, shots, notes)
FILE_META: dict[str, tuple[str, int, str]] = {
    "differentTime":               ("2025-02-09", 100, "imported,date_approximate"),
    "March8th_10_batch":           ("2025-03-08", 100, "imported"),
    "March11th_10_batch":          ("2025-03-11", 100, "imported"),
    "March11th_25_batch":          ("2025-03-11", 100, "imported"),
    "March16th_10_batch":          ("2025-03-16", 100, "imported"),
    "March16th_25_batch":          ("2025-03-16", 100, "imported"),
    "March16th_10_batch_500shots": ("2025-03-16", 500, "imported"),
    "March18th_10_batch":          ("2025-03-18", 100, "imported"),
    "March18th_10_batch_500shots": ("2025-03-18", 500, "imported"),
    "Jun16th_10_batch":            ("2025-06-16", 100, "imported"),
}

CSV_COLUMNS = [
    "run_date", "platform", "backend", "input_bits", "circuit_length",
    "shots", "counts_json", "success_probability", "job_id",
    "job_start_time", "job_end_time", "sdk_version", "notes",
]


def main() -> None:
    rows = []
    for csv_path in sorted(ARCHIVE_DIR.glob("success_probability_qiskit_*.csv")):
        key = csv_path.stem.removeprefix("success_probability_qiskit_")
        if key not in FILE_META:
            print(f"  WARNING: no metadata for {csv_path.name}, skipping", file=sys.stderr)
            continue

        run_date, shots, notes = FILE_META[key]
        df = pd.read_csv(csv_path, dtype={"input_bits": str})

        for _, row in df.iterrows():
            rows.append({
                "run_date": run_date,
                "platform": PLATFORM,
                "backend": BACKEND,
                "input_bits": str(row["input_bits"]).zfill(2),
                "circuit_length": int(row["circuit_length"]),
                "shots": shots,
                "counts_json": "{}",
                "success_probability": float(row["success_probability"]),
                "job_id": "",
                "job_start_time": "",
                "job_end_time": "",
                "sdk_version": "",
                "notes": notes,
            })

    result_df = pd.DataFrame(rows, columns=CSV_COLUMNS)
    result_df = result_df.sort_values(["run_date", "input_bits", "circuit_length"]).reset_index(drop=True)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(OUT_PATH, index=False)
    print(f"Wrote {len(result_df)} rows to {OUT_PATH}")

    by_date = (
        result_df.groupby("run_date")
        .agg(n=("success_probability", "count"), mean=("success_probability", "mean"))
    )
    by_date["mean"] = by_date["mean"].map(lambda x: f"{x * 100:.1f}%")
    print(by_date.to_string())


if __name__ == "__main__":
    main()
