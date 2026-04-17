---
title: IonQ
---

```js
import {successTimeSeries, volatilityTimeSeries, boxByLength, successByLength, successByInput, temporalDriftScatter} from "./components/platformCharts.js";
const data = await FileAttachment("data/ionq.json").json();
```

# IonQ

Trapped-ion QPU benchmarks run directly via the IonQ API. Data covers two hardware generations: **Aria-1** (accessed via AWS Braket, February–March 2024) and **Forte-1** (accessed directly, May–June 2025). Runs are currently paused.

<div style="display: flex; gap: 2rem; margin: 1rem 0;">
  <div class="platform-card" style="flex: 1">
    <div class="metric">${(data.runs.reduce((s, d) => s + d.mean_success, 0) / data.runs.length * 100).toFixed(1)}%</div>
    <div class="metric-label">Historical mean</div>
  </div>
  <div class="platform-card" style="flex: 1">
    <div class="metric">${data.runs.length}</div>
    <div class="metric-label">Total runs</div>
  </div>
  <div class="platform-card" style="flex: 1">
    <div class="metric">${data.circuits.length}</div>
    <div class="metric-label">Total circuits</div>
  </div>
</div>

## Success probability over time

Each point is the mean success rate across the circuits sampled that week. The shaded band shows ±1 standard deviation within the run.

```js
successTimeSeries(data, {color: "#74737B"})
```

## Consistency over time

Within-run standard deviation per week. Lower is more consistent.

```js
volatilityTimeSeries(data, {color: "#74737B"})
```

## Distribution by circuit depth

Box plots show the full distribution — median (center line), interquartile range (box), and outliers (dots). Wider boxes and lower medians at higher depths indicate noise accumulation with circuit complexity.

```js
boxByLength(data, {color: "#74737B"})
```

## Mean success by circuit depth

```js
successByLength(data, {color: "#74737B"})
```

## Mean success by input state

Does the initial qubit state affect results? Ideally it shouldn't — deviations suggest state-preparation or readout asymmetry.

```js
successByInput(data, {color: "#74737B"})
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
