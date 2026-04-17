# Condenser

**Longitudinal stability benchmarking of quantum computing platforms.**

This repository contains the benchmark circuits, automation, and raw results behind ISC's ongoing quantum platform stability study. It is a companion to ISC's published findings — not a tutorial or competitive ranking.

---

## What this measures

The quantum industry has many benchmarks that measure *capability* — circuit depth, qubit count, algorithmic accuracy at a point in time. This study measures something different: **operational consistency over time**.

The same simple circuits run weekly on each platform. The question we ask is not "how good is this platform?" but "how *stable* is it, week after week?" A platform that delivers 94% fidelity reliably is more useful in practice than one that swings between 80% and 99%.

This is a stability litmus test, not a bake-off. Platforms are never ranked against each other.

---

## The circuit family

Each run samples from a family of 24 two-qubit circuits: alternating CNOT sequences of lengths 1–6 applied to each of the four computational basis inputs (|00⟩, |01⟩, |10⟩, |11⟩). These circuits are deliberately simple — the goal is to isolate platform noise and drift, not to stress-test gate sets.

Per weekly run: 10 circuits drawn by stratified random sample, 100 shots each.

The correct output for each circuit is determined by exact simulation before each run. Success probability is the fraction of shots that land on the correct bitstring.

---

## Primary metric: weekly stability index

For each circuit–outcome pair, we compute the standard deviation of the observed success probability across all weeks. These are averaged up to a per-platform **weekly stability index** — a single number that rises when results are erratic and falls when they are consistent.

Plotting this index through time reveals drift, maintenance windows, hardware changes, and recovery.

---

## Platforms

| Platform | Access path | Status |
|---|---|---|
| Rigetti Ankaa-3 | AWS Braket | Active (manual weekly runs) |
| AQT | Qiskit / qiskit-aqt-provider | Active (manual weekly runs) |
| IonQ Aria-1 | AWS Braket | Paused (budget) |
| IBM | Qiskit Runtime | Pending (locating existing results) |

---

## Data

Raw results are stored as CSV files in `data/<platform>/results.csv` and committed with each weekly run. Each row is one circuit execution: input state, circuit length, shot histogram, success probability, job metadata, and SDK version.

Results are not post-processed or normalized. Outliers are retained; weeks with documented platform incidents are flagged in the `notes` column.

---

## Repository structure

```
benchmarks/    circuit definitions and per-platform submission logic
data/          raw weekly results (CSV, one file per platform)
scripts/       workflow entry point
tests/         unit tests for circuit generation and data logic
infra/         IAM policy reference files for AWS setup
archive/       prior exploratory notebooks
```

---

## Related work

- [QED-C Application-Oriented Benchmarks](https://github.com/SRI-International/QC-App-Oriented-Benchmarks) — capability benchmarks across algorithm families
- [Quantum Economic Development Consortium](https://quantumconsortium.org/)

---

*To run the benchmarks yourself, see [infra/README.md](infra/README.md) for AWS/IAM setup and [dashboard/README.md](dashboard/README.md) for the dashboard.*

.
