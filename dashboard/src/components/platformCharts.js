import * as Plot from "npm:@observablehq/plot";

const DOMAIN_FLOOR = 0.7;

/**
 * Time series of weekly mean success probability with ±1σ band.
 */
export function successTimeSeries(data, {color = "#363D47", width = 900} = {}) {
  const runs = data.runs.map(d => ({...d, date: new Date(d.run_date)}));
  const yMin = Math.max(DOMAIN_FLOOR, Math.min(...runs.map(d => d.mean_success)) - 0.05);

  return Plot.plot({
    width,
    height: 300,
    marginLeft: 55,
    y: {
      domain: [yMin, 1.02],
      label: "Mean success probability",
      tickFormat: d => `${(d * 100).toFixed(0)}%`,
    },
    x: {type: "utc", label: null},
    marks: [
      Plot.ruleY([1], {stroke: "#e2e8f0", strokeDasharray: "4,4"}),
      Plot.areaY(runs, {
        x: "date",
        y1: d => Math.max(yMin, d.mean_success - d.std_success),
        y2: d => Math.min(1, d.mean_success + d.std_success),
        fill: color,
        fillOpacity: 0.12,
      }),
      Plot.line(runs, {
        x: "date", y: "mean_success",
        stroke: color, strokeWidth: 2, curve: "monotone-x",
      }),
      Plot.dot(runs, {
        x: "date", y: "mean_success",
        fill: color, r: 4, tip: true,
        title: d => `${d.run_date}\n${(d.mean_success * 100).toFixed(1)}% ± ${(d.std_success * 100).toFixed(1)}%\n${d.n_circuits} circuits`,
      }),
    ],
  });
}

/**
 * Volatility over time — run-level standard deviation, showing whether
 * the platform is becoming more or less consistent.
 */
export function volatilityTimeSeries(data, {color = "#363D47", width = 900} = {}) {
  const runs = data.runs
    .filter(d => d.std_success > 0)
    .map(d => ({...d, date: new Date(d.run_date)}));

  return Plot.plot({
    width,
    height: 220,
    marginLeft: 55,
    y: {
      label: "Within-run std dev",
      tickFormat: d => `${(d * 100).toFixed(1)}%`,
    },
    x: {type: "utc", label: null},
    marks: [
      Plot.areaY(runs, {
        x: "date", y: "std_success",
        fill: color, fillOpacity: 0.15, curve: "monotone-x",
      }),
      Plot.line(runs, {
        x: "date", y: "std_success",
        stroke: color, strokeWidth: 1.5, curve: "monotone-x",
      }),
      Plot.dot(runs, {
        x: "date", y: "std_success",
        fill: color, r: 3, tip: true,
        title: d => `${d.run_date}\nσ = ${(d.std_success * 100).toFixed(1)}%`,
      }),
    ],
  });
}

/**
 * Box plot of success probability by circuit depth.
 * Shows distribution shape (median, IQR, whiskers, outliers) — richer than bar chart.
 */
export function boxByLength(data, {color = "#363D47", width = 560} = {}) {
  return Plot.plot({
    width,
    height: 280,
    marginLeft: 55,
    x: {label: "Circuit depth (# CNOTs)", tickFormat: d => `${d}`},
    y: {
      domain: [DOMAIN_FLOOR, 1.02],
      label: "Success probability",
      tickFormat: d => `${(d * 100).toFixed(0)}%`,
    },
    color: {range: [color]},
    marks: [
      Plot.ruleY([1], {stroke: "#e2e8f0", strokeDasharray: "4,4"}),
      Plot.boxY(data.circuits, {
        x: "circuit_length",
        y: "success_probability",
        fill: color,
        fillOpacity: 0.3,
        stroke: color,
      }),
    ],
  });
}

/**
 * Bar chart of mean success probability by circuit depth.
 * Uses y1/y2 to anchor bars at the domain floor (avoids x-axis overlap).
 */
export function successByLength(data, {color = "#363D47", width = 560} = {}) {
  return Plot.plot({
    width,
    height: 260,
    marginLeft: 55,
    x: {label: "Circuit depth (# CNOTs)", tickFormat: d => `${d}`},
    y: {
      domain: [DOMAIN_FLOOR, 1.02],
      label: "Mean success probability",
      tickFormat: d => `${(d * 100).toFixed(0)}%`,
    },
    marks: [
      Plot.ruleY([1], {stroke: "#e2e8f0", strokeDasharray: "4,4"}),
      Plot.ruleY([DOMAIN_FLOOR], {stroke: "#ccc"}),
      Plot.barY(data.by_length, {
        x: "length",
        y1: DOMAIN_FLOOR,
        y2: "mean_success",
        fill: color,
        fillOpacity: 0.8,
        tip: true,
        title: d => `Depth ${d.length}\n${(d.mean_success * 100).toFixed(1)}% mean\n${d.n} circuits`,
      }),
    ],
  });
}

/**
 * Bar chart of mean success probability by input state.
 * Uses y1/y2 to anchor bars at the domain floor (avoids x-axis overlap).
 */
export function successByInput(data, {color = "#363D47", width = 400} = {}) {
  return Plot.plot({
    width,
    height: 260,
    marginLeft: 55,
    x: {label: "Input state"},
    y: {
      domain: [DOMAIN_FLOOR, 1.02],
      label: "Mean success probability",
      tickFormat: d => `${(d * 100).toFixed(0)}%`,
    },
    marks: [
      Plot.ruleY([1], {stroke: "#e2e8f0", strokeDasharray: "4,4"}),
      Plot.ruleY([DOMAIN_FLOOR], {stroke: "#ccc"}),
      Plot.barY(data.by_input, {
        x: "input_bits",
        y1: DOMAIN_FLOOR,
        y2: "mean_success",
        fill: color,
        fillOpacity: 0.8,
        tip: true,
        title: d => `|${d.input_bits}⟩\n${(d.mean_success * 100).toFixed(1)}% mean\n${d.n} circuits`,
      }),
    ],
  });
}

/**
 * Temporal drift scatter — per-circuit completion time vs success probability.
 * Reveals whether quality degrades or varies systematically within a run.
 * Color-coded by circuit depth.
 */
export function temporalDriftScatter(data, {width = 900} = {}) {
  const circuits = data.circuits
    .filter(d => d.job_end_time)
    .map(d => ({...d, end_time: new Date(d.job_end_time)}));

  if (circuits.length === 0) return html`<p style="color: var(--isc-muted)">No timestamp data available.</p>`;

  return Plot.plot({
    width,
    height: 300,
    marginLeft: 55,
    y: {
      domain: [DOMAIN_FLOOR, 1.02],
      label: "Success probability",
      tickFormat: d => `${(d * 100).toFixed(0)}%`,
    },
    x: {type: "utc", label: "Circuit completion time"},
    color: {
      type: "ordinal",
      domain: [1, 2, 3, 4, 5, 6],
      label: "Circuit depth",
      legend: true,
    },
    marks: [
      Plot.ruleY([1], {stroke: "#e2e8f0", strokeDasharray: "4,4"}),
      Plot.dot(circuits, {
        x: "end_time",
        y: "success_probability",
        fill: "circuit_length",
        r: 4,
        fillOpacity: 0.7,
        tip: true,
        title: d => `Depth ${d.circuit_length} · |${d.input_bits}⟩\n${(d.success_probability * 100).toFixed(0)}%\n${d.run_date}`,
      }),
    ],
  });
}
