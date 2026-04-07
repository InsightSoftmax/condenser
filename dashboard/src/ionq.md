---
title: IonQ Aria-1
---

```js
import {successTimeSeries, successByLength, successByInput} from "./components/platformCharts.js";
const data = await FileAttachment("data/ionq.json").json();
```

# IonQ Aria-1

Trapped-ion QPU accessed via AWS Braket. Historical data from February–March 2024. Runs are currently paused.

<div style="display: flex; gap: 2rem; margin: 1rem 0;">
  <div class="platform-card" style="flex: 1">
    <div class="metric">${(data.runs.reduce((s, d) => s + d.mean_success, 0) / data.runs.length * 100).toFixed(1)}%</div>
    <div class="metric-label">Historical mean</div>
  </div>
  <div class="platform-card" style="flex: 1">
    <div class="metric">${data.runs.length}</div>
    <div class="metric-label">Runs (2024)</div>
  </div>
  <div class="platform-card" style="flex: 1">
    <div class="metric">${data.circuits.length}</div>
    <div class="metric-label">Total circuits</div>
  </div>
</div>

## Success probability over time

```js
successTimeSeries(data, {color: "#74737B"})
```

## Breakdown by circuit depth

```js
successByLength(data, {color: "#74737B"})
```

## Breakdown by input state

```js
successByInput(data, {color: "#74737B"})
```
