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
const sortedSummary = [...summary].sort((a, b) => {
  const order = s => s === "active" ? 0 : 1;
  const so = order(a.status) - order(b.status);
  return so !== 0 ? so : a.platform.localeCompare(b.platform);
});
```

<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1rem; margin: 1.5rem 0;">
${sortedSummary.map(p => html`
  <div class="platform-card">
    <div class="platform-name" style="display:flex;flex-direction:column;align-items:flex-start;gap:0.35rem">
      ${p.platform === "rigetti_cepheus" ? html`<a href="/rigetti">Rigetti ${p.backend}</a>` :
        p.platform === "rigetti_ankaa"   ? html`<a href="/rigetti-ankaa">Rigetti ${p.backend}</a>` :
        p.platform === "aqt"             ? html`<a href="/aqt">AQT ${p.backend}</a>` :
        p.platform === "ibm"             ? html`<a href="/ibm">IBM ${p.backend}</a>` :
        p.platform === "ionq_forte"      ? html`<a href="/ionq-forte">IonQ ${p.backend}</a>` :
                                           html`<a href="/ionq">IonQ ${p.backend}</a>`}
      <span class="badge ${statusClass[p.status]}">${statusLabel[p.status]}</span>
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

## Consistency over time

Within-run standard deviation per run — lower is more consistent.

```js
const PLATFORM_LABEL = {
  aqt: "AQT IBEX", ibm: "IBM Brisbane",
  ionq: "IonQ Aria-1", ionq_forte: "IonQ Forte-1",
  rigetti_ankaa: "Rigetti Ankaa-3", rigetti_cepheus: "Rigetti Cepheus-1-108Q",
};
const PLATFORM_COLOR = {
  aqt: "#363D47", ibm: "#1192E8",
  ionq: "#74737B", ionq_forte: "#99979D",
  rigetti_ankaa: "#A07800", rigetti_cepheus: "#CC8A00",
};
const allRuns = summary.flatMap(p =>
  p.sparkline.map(d => ({...d, label: PLATFORM_LABEL[p.platform] ?? p.platform, date: new Date(d.date)}))
);
const volatilityRuns = allRuns.filter(d => d.std > 0);
const colorDomain = Object.values(PLATFORM_LABEL);
const colorRange  = Object.values(PLATFORM_COLOR);
```

```js
Plot.plot({
  width: 900,
  height: 220,
  marginLeft: 55,
  y: {label: "Within-run std dev", tickFormat: d => `${(d * 100).toFixed(1)}%`},
  x: {type: "utc", label: null},
  color: {domain: colorDomain, range: colorRange, legend: true},
  marks: [
    Plot.line(volatilityRuns, {
      x: "date", y: "std", stroke: "label",
      strokeWidth: 1.5, curve: "monotone-x",
    }),
    Plot.dot(volatilityRuns, {
      x: "date", y: "std", fill: "label",
      r: 3, tip: true,
      title: d => `${d.label}\n${d.date.toLocaleDateString()}\nσ = ${(d.std * 100).toFixed(1)}%`,
    }),
  ],
})
```

## Success probability over time

```js
Plot.plot({
  width: 900,
  height: 280,
  marginLeft: 55,
  y: {domain: [0.7, 1.02], label: "Mean success probability", tickFormat: d => `${(d*100).toFixed(0)}%`},
  x: {type: "utc", label: null},
  color: {domain: colorDomain, range: colorRange, legend: true},
  marks: [
    Plot.ruleY([1], {stroke: "#e2e8f0"}),
    Plot.line(allRuns, {
      x: "date", y: "value", stroke: "label",
      strokeWidth: 2, curve: "monotone-x",
    }),
    Plot.dot(allRuns, {
      x: "date", y: "value", fill: "label",
      r: 3, tip: true,
      title: d => `${d.label}\n${d.date.toLocaleDateString()}\n${(d.value * 100).toFixed(1)}%`,
    }),
  ],
})
```

## Cost per benchmark run

10 circuits × 100 shots. Pricing as of April 2026.

```js
const PLATFORM_NAME = {
  aqt: "AQT IBEX (direct)", ibm: "IBM Brisbane",
  ionq: "IonQ Aria-1", ionq_forte: "IonQ Forte-1",
  rigetti_ankaa: "Rigetti Ankaa-3", rigetti_cepheus: "Rigetti Cepheus-1-108Q",
};
const ACCESS = {
  aqt: "qiskit-aqt-provider", ibm: "Qiskit Runtime (historical)",
  ionq: "AWS Braket (historical)", ionq_forte: "IonQ REST API (historical)",
  rigetti_ankaa: "AWS Braket (historical)", rigetti_cepheus: "AWS Braket",
};
const costRows = [
  ...summary.filter(p => p.cost_per_run_usd != null).map(p => ({
    platform: PLATFORM_NAME[p.platform] ?? p.platform,
    access: ACCESS[p.platform] ?? "—",
    status: p.status,
    cost_per_run: p.cost_per_run_usd,
    annual_52: p.cost_per_run_usd * 52,
  })),
  {platform: "AQT IBEX (via Braket)", access: "AWS Braket", status: "alternative",
   cost_per_run: 26.50, annual_52: 26.50 * 52},
];
const sortedCostRows = [...costRows].sort((a, b) => {
  const order = s => s === "active" ? 0 : 1;
  const so = order(a.status) - order(b.status);
  return so !== 0 ? so : a.platform.localeCompare(b.platform);
});
```

```js
Inputs.table(sortedCostRows, {
  select: false,
  columns: ["platform", "access", "status", "cost_per_run", "annual_52"],
  header: {platform: "Platform", access: "Access", status: "Status", cost_per_run: "Per run", annual_52: "Annual (52×)"},
  format: {
    status: d => html`<span class="badge ${d === "active" ? "badge-active" : "badge-historical"}">${d === "active" ? "Active" : "Paused"}</span>`,
    cost_per_run: d => `$${d.toFixed(2)}`,
    annual_52: d => `$${d.toFixed(0)}`,
  },
})
```

*AQT pricing from quotation Q2511001 (Nov 2025), converted at EUR/USD ≈ 1.09. IonQ figure is historical (Aria-1 at $0.03/shot); current Forte would be ~$83/run.*

---

*Benchmarks run weekly. Each run samples 10 circuits from a family of 24 (6 circuit depths × 4 input states), 100 shots each.*

<a href="/about" style="display:inline-block;margin-top:0.25rem;font-size:0.9rem;color:var(--isc-gold);font-weight:600;text-decoration:none;border-bottom:1.5px solid var(--isc-gold)">Learn more about the methodology →</a>
