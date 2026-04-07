---
title: AQT ibex
---

```js
import {successTimeSeries, successByLength, successByInput} from "./components/platformCharts.js";

// AQT data loader — reuse the same pattern as rigetti
const resp = await fetch("data/summary.json");
const summary = await resp.json();
const aqtSummary = summary.find(p => p.platform === "aqt");
```

# AQT ibex

Trapped-ion QPU accessed directly via `qiskit-aqt-provider`. Hardware access window: Tuesdays and Wednesdays 10:00–17:00 CET.

```js
if (!aqtSummary?.n_circuits) {
  display(html`<div class="platform-card" style="margin: 2rem 0">
    <strong>No data yet.</strong> AQT runs are starting in April 2026. Check back after the first automated run.
  </div>`);
} else {
  display(html`<p>Data available — add detail charts here.</p>`);
}
```
