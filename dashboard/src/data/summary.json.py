"""
Data loader: cross-platform summary for the overview page.
"""
import json
import sys
from pathlib import Path

import pandas as pd

repo_root = Path(__file__).parents[3]

PLATFORMS = {
    "rigetti": {"backend": "Ankaa-3", "status": "active",     "cost_per_run_usd": 3.90},
    "aqt":     {"backend": "IBEX",    "status": "active",     "cost_per_run_usd": 25.07},
    "ionq":    {"backend": "Aria-1",  "status": "historical", "cost_per_run_usd": 33.00},
}

summary = []

for platform, meta in PLATFORMS.items():
    csv_path = repo_root / "data" / platform / "results.csv"
    if not csv_path.exists():
        summary.append({
            "platform": platform,
            "backend": meta["backend"],
            "status": meta["status"],
            "cost_per_run_usd": meta["cost_per_run_usd"],
            "latest_run": None,
            "latest_success": None,
            "overall_mean": None,
            "n_runs": 0,
            "n_circuits": 0,
            "sparkline": [],
        })
        continue

    df = pd.read_csv(csv_path, parse_dates=["run_date"], dtype={"input_bits": str})
    df = df[df["notes"].fillna("") == ""]

    if platform == "ionq":
        df = df[df["backend"].str.contains("Aria", na=False)]

    if df.empty:
        summary.append({
            "platform": platform,
            "backend": meta["backend"],
            "status": meta["status"],
            "latest_run": None,
            "latest_success": None,
            "overall_mean": None,
            "n_runs": 0,
            "n_circuits": 0,
            "sparkline": [],
        })
        continue

    runs = (
        df.groupby("run_date")["success_probability"]
        .mean()
        .reset_index()
        .sort_values("run_date")
    )

    sparkline = [
        {"date": row["run_date"].strftime("%Y-%m-%d"), "value": round(row["success_probability"], 4)}
        for _, row in runs.iterrows()
    ]

    latest_run = runs["run_date"].max()
    latest_success = runs.loc[runs["run_date"] == latest_run, "success_probability"].values[0]

    summary.append({
        "platform": platform,
        "backend": meta["backend"],
        "status": meta["status"],
        "cost_per_run_usd": meta["cost_per_run_usd"],
        "latest_run": latest_run.strftime("%Y-%m-%d"),
        "latest_success": round(float(latest_success), 4),
        "overall_mean": round(float(df["success_probability"].mean()), 4),
        "n_runs": int(runs.shape[0]),
        "n_circuits": int(df.shape[0]),
        "sparkline": sparkline,
    })

json.dump(summary, sys.stdout)
