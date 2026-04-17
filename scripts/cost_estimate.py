"""
Estimate the cost of running the condenser benchmark suite.

Pricing is hardcoded with a verification date. Check provider pages before budgeting.

  AWS Braket QPU pricing:  https://aws.amazon.com/braket/pricing/
  AQT direct pricing:      Quotation Q2511001 (archive/Q2511001.pdf), dated 2025-11-04
                           0.30 EUR/circuit + 0.02 EUR/shot on IBEX Q1

Usage:
    uv run python scripts/cost_estimate.py
    uv run python scripts/cost_estimate.py --shots 200 --circuits 20 --weeks 26
"""

import argparse
import sys

# ── Benchmark parameters ──────────────────────────────────────────────────────

DEFAULT_N_CIRCUITS = 10   # circuits per weekly run (stratified sample of 24)
DEFAULT_SHOTS = 100        # shots per circuit
DEFAULT_WEEKS = 52         # weeks per year

EUR_TO_USD = 1.09          # approximate; update as needed

# ── AWS Braket QPU pricing ────────────────────────────────────────────────────
# Source: https://aws.amazon.com/braket/pricing/
# Verified: 2026-04-04
#
# Charges apply per quantum task (circuit submission) plus per shot (execution).
# S3 storage for result files is negligible (<1 KB per task).

BRAKET_PRICING: dict[str, dict] = {
    "Rigetti Ankaa-3": {
        "per_task_usd":   0.30,
        "per_shot_usd":   0.00090,
        "region":         "us-west-1",
        "access":         "AWS Braket",
        "status":         "active",
        "module":         "rigetti_braket",
        "runs_per_year":  52,   # weekly
    },
    "IQM Garnet": {
        "per_task_usd":   0.30,
        "per_shot_usd":   0.00145,
        "region":         "eu-north-1",
        "access":         "AWS Braket",
        "status":         "active",
        "module":         "iqm_braket",
        "runs_per_year":  52,   # weekly
    },
    "IonQ Forte-1 (via Braket)": {
        "per_task_usd":   0.30,
        "per_shot_usd":   0.08000,
        "region":         "us-east-1",
        "access":         "AWS Braket",
        "status":         "active",
        "module":         "ionq_braket",
        "runs_per_year":  12,   # monthly (15th of month)
        "notes":          "Historical data used IonQ Aria-1 (~$0.03/shot) and Harmony."
                          " Forte-1 is the current Braket-listed IonQ device.",
    },
    "IonQ Forte-1 (direct REST API)": {
        "per_task_usd":   25.88,   # observed: $7,762 / 300 circuits from Claire's account (2025)
        "per_shot_usd":   0.00,    # gate + shot charges rolled into per_task_usd observation
        "region":         "IonQ cloud (direct)",
        "access":         "ionq_direct (REST API, IONQ_API_KEY)",
        "status":         "active",
        "module":         "ionq_direct",
        "runs_per_year":  12,   # monthly (1st of month)
        "notes":          "Cost derived from observed billing: $7,762 for 300 circuits."
                          " IonQ charges per gate + per shot; exact rate not published."
                          " Verify current pricing at https://ionq.com/pricing.",
    },
    "AQT IBEX-Q1 (direct, qiskit-aqt-provider)": {
        "per_task_usd":   0.30 * EUR_TO_USD,   # 0.30 EUR/circuit
        "per_shot_usd":   0.02 * EUR_TO_USD,    # 0.02 EUR/shot
        "region":         "Innsbruck (direct)",
        "access":         "qiskit-aqt-provider",
        "status":         "active",
        "module":         "aqt_qiskit",
        "runs_per_year":  52,   # weekly
        "notes":          "Source: quotation Q2511001 (2025-11-04). EUR/USD ≈ 1.09."
                          " Hardware backend name must be confirmed with Arash"
                          " (run provider.backends() to see options).",
    },
    "IBM Brisbane (ibm_brisbane)": {
        "per_task_usd":   0.00,
        "per_shot_usd":   0.00,
        "region":         "IBM Cloud (US)",
        "access":         "Qiskit Runtime (ibm_quantum channel)",
        "status":         "active",
        "module":         "ibm_qiskit",
        "notes":          "IBM Standard Plan charges by QPU execution time (seconds),"
                          " not per-task/shot. Estimated ~$0.10–0.50/run for 10 circuits."
                          " See https://quantum.ibm.com/services/programs/sampler for"
                          " current pricing. Requires IBM_QUANTUM_TOKEN secret.",
    },
    "AQT IBEX-Q1 (via Braket)": {
        "per_task_usd":   0.30,
        "per_shot_usd":   0.02350,
        "region":         "eu-north-1",
        "access":         "AWS Braket",
        "status":         "alternative",
        "runs_per_year":  52,
        "notes":          "Braket access available as an alternative to direct."
                          " Pricing is within ~5% of direct (direct is slightly cheaper).",
    },
}

# ── Per-run cost calculation ──────────────────────────────────────────────────

def cost_per_run(per_task: float, per_shot: float,
                 n_circuits: int, shots: int) -> tuple[float, float, float]:
    task_cost = n_circuits * per_task
    shot_cost = n_circuits * shots * per_shot
    return task_cost, shot_cost, task_cost + shot_cost


def format_usd(amount: float) -> str:
    if amount < 1:
        return f"${amount:.4f}"
    return f"${amount:.2f}"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--circuits", type=int, default=DEFAULT_N_CIRCUITS,
                        help=f"Circuits per run (default: {DEFAULT_N_CIRCUITS})")
    parser.add_argument("--shots", type=int, default=DEFAULT_SHOTS,
                        help=f"Shots per circuit (default: {DEFAULT_SHOTS})")
    parser.add_argument("--weeks", type=int, default=DEFAULT_WEEKS,
                        help=f"Runs per year (default: {DEFAULT_WEEKS})")
    args = parser.parse_args(argv)

    n_circuits = args.circuits
    shots = args.shots
    weeks = args.weeks

    print("=" * 65)
    print("  Condenser benchmark cost estimate")
    print("=" * 65)
    print(f"  Configuration : {n_circuits} circuits × {shots} shots each")
    print(f"  Frequency     : {weeks} runs/year (weekly = 52)")
    print("  Pricing date  : 2026-04-04  (verify at provider pages)")
    print()

    for name, p in BRAKET_PRICING.items():
        task_cost, shot_cost, total = cost_per_run(
            p["per_task_usd"], p["per_shot_usd"], n_circuits, shots
        )
        runs = p.get("runs_per_year", weeks)
        annual = total * runs
        freq = "weekly" if runs == 52 else f"monthly ({runs}/yr)" if runs == 12 else f"{runs}/yr"

        print(f"  {name}  [{p['status']}]")
        print(f"    Access      : {p['access']}  ({p['region']})")
        print(f"    Per task    : {format_usd(p['per_task_usd'])}  |  "
              f"per shot: {format_usd(p['per_shot_usd'])}")
        print(f"    Per run     : {format_usd(total)}  "
              f"({format_usd(task_cost)} tasks + {format_usd(shot_cost)} shots)")
        print(f"    Annual      : {format_usd(annual)}  ({freq})")
        if p.get("notes"):
            print(f"    Note        : {p['notes']}")
        print()

    # Summary for active platforms only
    active = {k: v for k, v in BRAKET_PRICING.items()
              if v["status"] == "active"}
    if active:
        total_annual = sum(
            cost_per_run(p["per_task_usd"], p["per_shot_usd"], n_circuits, shots)[2]
            * p.get("runs_per_year", weeks)
            for p in active.values()
        )
        print("-" * 65)
        print(f"  Active platforms combined: {format_usd(total_annual)}/year")
        print()

    print("  Notes:")
    print("  · Circuit family: 4 input states × 6 CNOT lengths = 24 distinct circuits.")
    print("    Each run draws a stratified sample of 10 (one from each length guaranteed).")
    print("  · AQT direct pricing from quotation Q2511001 (archive/Q2511001.pdf).")
    print(f"    EUR amounts converted at EUR/USD = {EUR_TO_USD}.")
    print("  · AQT hardware backend name must be confirmed with Arash")
    print("    before automating. Run provider.backends() to see available options.")
    print("  · S3 storage for result files is negligible (<1 KB per task).")
    print("  · IonQ Harmony / Aria-1 are no longer listed on Braket; Forte")
    print("    is the current offering. Historical data used Harmony (1000 shots).")
    print("=" * 65)


if __name__ == "__main__":
    main(sys.argv[1:])
