---
title: Rigetti Ankaa-3
---

```js
import {successTimeSeries, volatilityTimeSeries, boxByLength, successByLength, successByInput, temporalDriftScatter} from "./components/platformCharts.js";
const data = await FileAttachment("data/rigetti.json").json();
```

# Rigetti Ankaa-3

Superconducting QPU accessed via AWS Braket. Runs weekly on Tuesdays.

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
    <div class="metric-label">Weekly runs</div>
  </div>
  <div class="platform-card" style="flex: 1">
    <div class="metric">${data.circuits.length}</div>
    <div class="metric-label">Total circuits</div>
  </div>
</div>

## Success probability over time

Each point is the mean success rate across the 10 circuits sampled that week. The shaded band shows ±1 standard deviation within the run.

```js
successTimeSeries(data, {color: "#CC8A00"})
```

## Consistency over time

Within-run standard deviation per week. Lower is more consistent. Upward trend indicates growing variability.

```js
volatilityTimeSeries(data, {color: "#CC8A00"})
```

## Distribution by circuit depth

Box plots show the full distribution — median (center line), interquartile range (box), and outliers (dots). Wider boxes and lower medians at higher depths indicate noise accumulation with circuit complexity.

```js
boxByLength(data, {color: "#CC8A00"})
```

## Mean success by circuit depth

```js
successByLength(data, {color: "#CC8A00"})
```

## Mean success by input state

Does the initial qubit state affect results? Ideally it shouldn't — deviations suggest state-preparation or readout asymmetry.

```js
successByInput(data, {color: "#CC8A00"})
```

## Temporal drift within runs

Per-circuit completion time vs. success probability, colored by circuit depth. Systematic patterns (e.g., quality worsening over time within a run) indicate hardware drift during execution.

```js
temporalDriftScatter(data)
```

## Recent runs

```js
const recent = data.runs.slice(-12).reverse();
Inputs.table(recent, {
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
