# condenser — Claude Code Instructions

## Project Purpose

Longitudinal stability benchmarking of quantum computing platforms. **This is not a performance bake-off.** We run the same simple "litmus test" circuits weekly on each platform and track how consistent results are over time — drift, volatility, predictability.

Each platform is analyzed only against its own prior runs, never ranked against other platforms.

## Tech Stack

- **Python** — primary language
- **uv / uvx** — always use these for environment and dependency management; never use pip directly or create venvs manually
- **ruff** — linting and formatting (replaces flake8/black/isort)
- **pytest** — testing framework
- **pandas** — data manipulation
- **matplotlib / seaborn** — visualization
- **Quantum SDKs** — determined per platform (e.g., `amazon-braket-sdk` for IonQ via AWS; Qiskit for IBM, etc.)

## Automation: GitHub Actions (not SageMaker/Lambda)

Benchmarks run as scheduled GitHub Actions workflows — **not** SageMaker notebooks triggered by Lambda. There is no technical reason to run inside AWS; the Braket SDK is just a Python library making authenticated HTTPS calls.

### Two-stage workflow (submit → collect)

QPU queues can be measured in **days** (IonQ in particular). A single blocking workflow would time out. Instead:

1. **Submit** (`.github/workflows/submit-benchmark.yml`) — runs weekly. Submits circuits, writes job IDs + circuit metadata to `pending/<platform>/<date>.json`, commits and exits immediately.
2. **Collect** (`.github/workflows/collect-results.yml`) — runs every 6 hours. Checks all files in `pending/`. For each batch where all jobs are done, fetches results, appends to `data/<platform>/results.csv`, and removes the pending file. If jobs are still queued, exits silently and retries at the next 6-hour tick.

State between runs lives entirely in the `pending/` directory, committed to the repo. No external state store needed.

### AWS authentication: OIDC federation (no stored AWS credentials)

Do **not** store `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` as secrets. Instead use GitHub's OIDC provider to assume an IAM role scoped to this repo and branch. The action gets a short-lived token automatically.

IAM setup files live in `infra/`:
- `infra/iam-policy.json` — minimum Braket + S3 permissions
- `infra/iam-trust-policy.json` — OIDC trust policy scoped to `InsightSoftmax/condenser` main branch

### Other platform credentials (IonQ direct, IBM, etc.)

Store as **GitHub Environment secrets** in the `quantum-production` environment, not as repository-level secrets.

## Security: Public Repo

This repo is public. Key mitigations:

1. **GitHub Environment `quantum-production`** — all QPU secrets live here, not at repo level
2. **Deployment branch rule** — restrict the environment to the `main` branch only; fork PRs cannot access it
3. **`id-token: write` permission** — required for OIDC; scoped only to the benchmark job
4. **No `pull_request_target` trigger** — never use this trigger; it runs with secrets in the context of the base repo even for fork PRs
5. **No secret printing** — never `print()` or `echo` secret values in workflow steps or benchmark scripts
6. **Cost gate** — the `quantum-production` environment should have required reviewers enabled for `workflow_dispatch` runs; scheduled runs from `main` are safe without manual approval

## Data Storage

Results are stored as **CSV files per platform**, committed to git. No database. One row per circuit execution.

### CSV schema
```
run_date, platform, backend, input_bits, circuit_length, shots,
counts_json, success_probability, job_id, job_start_time, job_end_time,
sdk_version, notes
```

`counts_json` is the raw shot histogram as a JSON string, e.g. `{"00":45,"01":25,"10":18,"11":12}`.

Data lives in `data/<platform>/results.csv`.

## Circuit Family

24 circuits: **6 lengths** (1–6 CNOTs) × **4 input states** (00, 01, 10, 11).

Each circuit is an alternating CNOT sequence: CNOT(0→1), CNOT(1→0), CNOT(0→1), ... The reference (correct) output for each circuit is determined by simulation before the QPU run.

Per run: sample **10 circuits** stratified across lengths/states, **100 shots** each.

## Platforms

| Platform | Module | Access path | Status |
|---|---|---|---|
| Rigetti Ankaa-3 | `rigetti_braket` | AWS Braket (OIDC/IAM) | Active — automated weekly (Tuesdays 10:00 UTC) |
| AQT | `aqt_qiskit` | Qiskit + qiskit-aqt-provider (`AQT_API_KEY`) | Active — automated weekly (Tuesdays 10:00 UTC); hardware window Tue/Wed 10:00–17:00 CET |
| IonQ Aria-1 | `ionq_braket` | AWS Braket (OIDC/IAM) | Paused (budget) |
| IBM Brisbane | `ibm_qiskit` | Qiskit Runtime (`IBM_QUANTUM_TOKEN`) | Active — automated monthly; historical data Feb–Jun 2025 (Sami); org account is `Qiskit Runtime - Standard` (pay-as-you-go) |

## Project Structure

```
benchmarks/          # one Python module per platform
  circuits.py        # shared: REFERENCE_TABLE, circuit builders, sampling
  ionq_braket.py
  rigetti_braket.py
  aqt_qiskit.py
  ibm_qiskit.py
data/                # CSV results per platform (committed to git)
  rigetti/results.csv
  aqt/results.csv
  ...
pending/             # submitted job IDs awaiting collection (committed to git)
  rigetti/2026-04-01.json
  ...
infra/               # IAM policy reference files and setup instructions
scripts/
  submit_benchmark.py   # called by submit-benchmark.yml
  collect_results.py    # called by collect-results.yml
tests/
.github/
  workflows/
    submit-benchmark.yml   # weekly: submit circuits, write pending files
    collect-results.yml    # every 6h: check pending, collect completed jobs
pyproject.toml       # managed by uv
CLAUDE.md
```

## Shared Circuit Logic

`benchmarks/circuits.py` contains everything platform-agnostic:
- `REFERENCE_TABLE` — hardcoded correct outputs for all 24 circuits (deterministic, no simulator needed)
- `sample_circuits(n)` — stratified random sample
- `build_circuit_braket(input_bits, length)` — Braket SDK circuit
- `build_circuit_qiskit(input_bits, length)` — Qiskit circuit

All platform modules import from here. Do not duplicate circuit logic in platform modules.

## Benchmark Module Interface

Each platform module in `benchmarks/` must export two functions:

```python
def submit(n_circuits: int = 10, shots: int = 100, dry_run: bool = False) -> dict:
    """
    Submit circuits. Returns a pending dict to be saved to pending/<platform>/<date>.json.
    Must not block waiting for results.
    """

def collect(pending: dict) -> list[dict] | None:
    """
    Check job status. Returns list of result dicts if all jobs complete,
    None if still waiting, raises RuntimeError on failure.
    """
```

The pending dict schema:
```json
{
  "run_date": "2026-03-28",
  "platform": "ionq",
  "backend": "IonQ Aria-1",
  "sdk_version": "1.88.0",
  "shots": 100,
  "submitted_at": "2026-03-28T12:00:00Z",
  "dry_run": false,
  "jobs": [
    {"job_id": "...", "input_bits": "01", "circuit_length": 3}
  ]
}
```

## Cost Guardrails

- **Always estimate cost before submitting to real QPUs.** Use provider preflight/cost tools where available.
- Simulators only during development and testing; mock QPU calls in tests.
- The `quantum-production` GitHub Environment acts as a human gate for manual runs.
