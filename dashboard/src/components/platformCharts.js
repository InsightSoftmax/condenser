import * as Plot from "npm:@observablehq/plot";

/**
 * Time series of weekly mean success probability with ±1σ band.
 */
export function successTimeSeries(data, {color = "#4a90d9", width = 900} = {}) {
  const runs = data.runs.map(d => ({...d, date: new Date(d.run_date)}));

  return Plot.plot({
    width,
    height: 300,
    marginLeft: 55,
    y: {
      domain: [Math.max(0, Math.min(...runs.map(d => d.mean_success)) - 0.05), 1.02],
      label: "Mean success probability",
      tickFormat: d => `${(d * 100).toFixed(0)}%`,
    },
    x: {type: "utc", label: null},
    marks: [
      Plot.ruleY([1], {stroke: "#e2e8f0", strokeDasharray: "4,4"}),
      // ±1σ band
      Plot.areaY(runs, {
        x: "date",
        y1: d => Math.max(0, d.mean_success - d.std_success),
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
 * Bar chart of mean success probability by circuit length.
 */
export function successByLength(data, {color = "#4a90d9", width = 560} = {}) {
  return Plot.plot({
    width,
    height: 260,
    marginLeft: 55,
    x: {label: "Circuit depth (# CNOTs)", tickFormat: d => `${d}`},
    y: {
      domain: [0.7, 1.02],
      label: "Mean success probability",
      tickFormat: d => `${(d * 100).toFixed(0)}%`,
    },
    marks: [
      Plot.ruleY([1], {stroke: "#e2e8f0", strokeDasharray: "4,4"}),
      Plot.barY(data.by_length, {
        x: "length", y: "mean_success",
        fill: color, fillOpacity: 0.85,
        tip: true,
        title: d => `Depth ${d.length}\n${(d.mean_success * 100).toFixed(1)}% mean\n${d.n} circuits`,
      }),
      Plot.ruleY([0]),
    ],
  });
}

/**
 * Bar chart of mean success probability by input state.
 */
export function successByInput(data, {color = "#4a90d9", width = 400} = {}) {
  return Plot.plot({
    width,
    height: 260,
    marginLeft: 55,
    x: {label: "Input state"},
    y: {
      domain: [0.7, 1.02],
      label: "Mean success probability",
      tickFormat: d => `${(d * 100).toFixed(0)}%`,
    },
    marks: [
      Plot.ruleY([1], {stroke: "#e2e8f0", strokeDasharray: "4,4"}),
      Plot.barY(data.by_input, {
        x: "input_bits", y: "mean_success",
        fill: color, fillOpacity: 0.85,
        tip: true,
        title: d => `|${d.input_bits}⟩\n${(d.mean_success * 100).toFixed(1)}% mean\n${d.n} circuits`,
      }),
      Plot.ruleY([0]),
    ],
  });
}
