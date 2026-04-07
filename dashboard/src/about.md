---
title: Methodology
---

# Methodology

## What Condenser measures

Condenser tracks **longitudinal stability** of quantum computing platforms — not a cross-platform performance ranking. We run the same simple circuits on each platform every week and ask: *how consistent are the results over time?*

Each platform is analyzed only against its own prior runs. Drift, volatility, and predictability are the signals we care about.

## The circuit family

We use a family of **24 circuits**: 6 circuit depths (1–6 CNOT gates) × 4 input states (|00⟩, |01⟩, |10⟩, |11⟩).

Each circuit is an alternating CNOT sequence:

```
CNOT(0→1), CNOT(1→0), CNOT(0→1), ...
```

The reference (correct) output for each circuit is determined by classical simulation. These are deliberately simple — the goal is to act as a litmus test, not to stress the hardware.

## Each weekly run

- **10 circuits** sampled from the 24, stratified across depths and input states
- **100 shots** per circuit
- Results compared against the reference output to compute **success probability**

## Success probability

For each circuit execution:

```
success_probability = (shots matching reference output) / (total shots)
```

A perfect QPU would score 1.0 on every circuit. Real hardware scores lower due to gate errors, decoherence, readout errors, and crosstalk.

## What the charts show

- **Time series**: each weekly run produces one data point — the mean success probability across the 10 sampled circuits
- **By circuit depth**: deeper circuits accumulate more gate errors; this chart shows how quickly fidelity falls off with depth
- **By input state**: ideally, results should not depend on the input — deviations suggest state-preparation or readout asymmetry

## Data

All raw results are stored as CSV files committed to the [condenser GitHub repository](https://github.com/InsightSoftmax/condenser). One row per circuit execution, including the full shot histogram (`counts_json`), timestamps, and SDK version.
