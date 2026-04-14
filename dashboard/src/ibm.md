---
title: IBM Brisbane
---

```js
import {successTimeSeries, volatilityTimeSeries, boxByLength, successByLength, successByInput, temporalDriftScatter} from "./components/platformCharts.js";
const data = await FileAttachment("data/ibm.json").json();
```

# IBM Brisbane

Superconducting QPU (Eagle r3, 127 qubits) accessed via Qiskit Runtime. Historical data from February–June 2025, collected by Sami. Future runs are automated monthly.

<div style="display: flex; gap: 2rem; margin: 1rem 0;">
  <div class="platform-card" style="flex: 1">
    <div class="metric">${(data.runs.at(-1)?.mean_success * 100).toFixed(1)}%</div>
    <div class="metric-label">Latest run success rate</div>
  </div>
  <div class="platform-card" style="flex: 1">
    <div class="metric">${(data.runs.reduce((s, d) => s + d.mean_success, 0) / data.runs.length * 100).toFixed(1)}%</div>
    <div class="metric-label">All-time mean</div>
  </div>
  <div class="platform-card" style="flex: 1">
    <div class="metric">${data.runs.length}</div>
    <div class="metric-label">Runs (2025)</div>
  </div>
  <div class="platform-card" style="flex: 1">
    <div class="metric">${data.circuits.length}</div>
    <div class="metric-label">Total circuits</div>
  </div>
</div>

## Success probability over time

Success probability for a given circuit is the fraction of shots that produced the correct output — where "correct" is the deterministic, noise-free answer computed by classical simulation. Each point is the mean across all circuits sampled in that run. The shaded band shows ±1 standard deviation within the run.

```js
successTimeSeries(data, {color: "#1192E8"})
```

## Consistency over time

Within-run standard deviation per run. Lower is more consistent.

```js
volatilityTimeSeries(data, {color: "#1192E8"})
```

## Distribution by circuit depth

Box plots show the full distribution — median (center line), interquartile range (box), and outliers (dots). Wider boxes and lower medians at higher depths indicate noise accumulation with circuit complexity.

```js
boxByLength(data, {color: "#1192E8"})
```

## Mean success by circuit depth

Mean success probability for each depth, averaged across all runs. A declining trend confirms that noise accumulates as circuit depth increases.

```js
successByLength(data, {color: "#1192E8"})
```

## Mean success by input state

Does the initial qubit state affect results? Ideally it shouldn't — deviations suggest state-preparation or readout asymmetry.

```js
successByInput(data, {color: "#1192E8"})
```

## Temporal drift within runs

Per-circuit completion time vs. success probability, colored by circuit depth. Systematic patterns indicate hardware drift during execution.

```js
temporalDriftScatter(data)
```

## All runs

```js
Inputs.table(data.runs.slice().reverse(), {
  columns: ["run_date", "mean_success", "std_success", "n_circuits"],
  header: {
    run_date: "Date",
    mean_success: "Mean success",
    std_success: "Std dev",
    n_circuits: "Circuits",
  },
  format: {
    mean_success: d => `${(d * 100).toFixed(1)}%`,
    std_success: d => `±${(d * 100).toFixed(1)}%`,
  },
})
```
