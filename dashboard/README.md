# Quantum Stability Monitor — Dashboard

Observable Framework static site displaying longitudinal QPU benchmarking results.

## Prerequisites

- Node.js 18+
- Python 3.11+ with `uv` (for data loaders)

Install Node dependencies:

```sh
npm install
```

## Development

```sh
npm run dev
```

Opens a live-reloading dev server at <http://127.0.0.1:3000>. Data loaders (the `.json.py` files in `src/data/`) run automatically when their output is requested. They read from `data/<platform>/results.csv` in the repo root.

## Build

```sh
npm run build
```

Outputs a fully static site to `dist/`. The build runs all data loaders and bakes their output into the bundle — no Python needed at serve time.

## Lint

```sh
npm run lint
```

Runs ESLint on `src/components/` and `observablehq.config.js`.

## Structure

```
dashboard/
  src/
    index.md              # Overview page — all platforms overlaid
    rigetti.md            # Rigetti Ankaa-3 detail page
    ionq.md               # IonQ Aria-1 detail page
    aqt.md                # AQT IBEX detail page
    about.md              # Methodology
    components/
      platformCharts.js   # Shared Observable Plot chart functions
    data/
      rigetti.json.py     # Data loader — reads data/rigetti/results.csv
      ionq.json.py        # Data loader — reads data/ionq/results.csv
      summary.json.py     # Data loader — cross-platform overview
    theme.css             # ISC brand styles
  observablehq.config.js
  package.json
```

## Data loaders

Each `.json.py` loader is a standalone Python script that writes JSON to stdout. Observable Framework calls them automatically during `dev` and `build`. They expect the repo root to be three levels up (`Path(__file__).parents[3]`).

To run a loader manually:

```sh
python dashboard/src/data/rigetti.json.py | python -m json.tool | head -40
```

## Deployment

The `dist/` folder is a plain static site — serve it from any static host (GitHub Pages, S3+CloudFront, Netlify, etc.). A GitHub Actions workflow for Pages deployment is planned.
