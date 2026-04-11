---
title: Overview
---

# Quantum Platform Stability

Weekly litmus-test circuits run on each platform. We track consistency over time — not a cross-platform ranking. Each platform is benchmarked only against its own prior runs.

```js
const summary = await FileAttachment("data/summary.json").json();
```

```js
// Platform cards
const statusLabel = {active: "Active", historical: "Paused", paused: "Paused"};
const statusClass = {active: "badge-active", historical: "badge-historical", paused: "badge-paused"};
```

<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1rem; margin: 1.5rem 0;">
${summary.map(p => html`
  <div class="platform-card">
    <div class="platform-name">
      ${p.platform === "rigetti" ? html`<a href="/rigetti">Rigetti ${p.backend}</a>` :
        p.platform === "aqt"     ? html`<a href="/aqt">AQT ${p.backend}</a>` :
                                   html`<a href="/ionq">IonQ ${p.backend}</a>`}
      <span class="badge ${statusClass[p.status]}" style="margin-left: 0.5rem">${statusLabel[p.status]}</span>
    </div>
    ${p.latest_success != null ? html`
      <div class="metric">${(p.latest_success * 100).toFixed(1)}%</div>
      <div class="metric-label">Latest run success rate</div>
      <div style="margin-top: 0.75rem; font-size: 0.85rem; color: var(--isc-muted)">
        ${p.n_runs} runs · ${p.n_circuits} circuits<br>last run ${p.latest_run}
      </div>
    ` : html`<div style="color: var(--isc-muted); font-size: 0.9rem">No data yet</div>`}
  </div>
`)}
</div>

## Success probability over time

```js
const allRuns = summary.flatMap(p =>
  p.sparkline.map(d => ({...d, platform: p.platform, date: new Date(d.date)}))
);
const platformColors = {rigetti: "#CC8A00", aqt: "#363D47", ionq: "#74737B"};
```

```js
Plot.plot({
  width: 900,
  height: 280,
  marginLeft: 50,
  y: {domain: [0.7, 1.02], label: "Mean success probability", tickFormat: d => `${(d*100).toFixed(0)}%`},
  x: {type: "utc", label: null},
  color: {domain: Object.keys(platformColors), range: Object.values(platformColors), legend: true},
  marks: [
    Plot.ruleY([1], {stroke: "#e2e8f0"}),
    Plot.line(allRuns, {
      x: "date", y: "value", stroke: "platform",
      strokeWidth: 2, curve: "monotone-x"
    }),
    Plot.dot(allRuns, {
      x: "date", y: "value", fill: "platform",
      r: 3, tip: true,
      title: d => `${d.platform}\n${d.date.toLocaleDateString()}\n${(d.value * 100).toFixed(1)}%`
    }),
  ]
})
```

## Cost per benchmark run

10 circuits × 100 shots. Pricing as of April 2026.

```js
Inputs.table(summary.map(p => ({
  platform: p.platform === "rigetti" ? "Rigetti Ankaa-3" :
            p.platform === "aqt"     ? "AQT IBEX" :
                                       "IonQ Aria-1",
  access: p.platform === "rigetti" ? "AWS Braket" :
          p.platform === "aqt"     ? "qiskit-aqt-provider (direct)" :
                                     "AWS Braket (historical)",
  cost_per_run: p.cost_per_run_usd,
  annual_52: p.cost_per_run_usd * 52,
})), {
  columns: ["platform", "access", "cost_per_run", "annual_52"],
  header: {platform: "Platform", access: "Access", cost_per_run: "Per run", annual_52: "Annual (52×)"},
  format: {
    cost_per_run: d => `$${d.toFixed(2)}`,
    annual_52: d => `$${d.toFixed(0)}`,
  },
})
```

*AQT pricing from quotation Q2511001 (Nov 2025), converted at EUR/USD ≈ 1.09. IonQ figure is historical (Aria-1 at $0.03/shot); current Forte would be ~$83/run.*

---

*Benchmarks run weekly. Each run samples 10 circuits from a family of 24 (6 circuit depths × 4 input states), 100 shots each. [Learn more about the methodology.](/about)*
