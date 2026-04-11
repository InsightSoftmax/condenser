"""
IonQ Forte-1 benchmark via the IonQ REST API.

Authentication: IONQ_API_KEY environment variable (GitHub secret in quantum-production).
Backend: IonQ Forte-1 (qpu.forte-1)
Project: quantum-stability (2237ddcc-2644-4dc1-b971-b3cbece475e1)

Each circuit is submitted as an individual job so each job_id maps directly to one
(input_bits, circuit_length) — no batch/child complexity.

IonQ result keys use LSB convention: qubit 0 is bit 0 of the integer key.
So key "2" = binary "10" reversed = our bitstring "01".

Forte-1 typically completes in ~13 seconds, so collect() will usually return
results on the first check after the 6-hour collect cycle.
"""

import json
import os
import time
from datetime import UTC, date, datetime

import requests

from benchmarks.circuits import REFERENCE_TABLE, sample_circuits

PLATFORM = "ionq"
BACKEND = "Forte-1"
TARGET = "qpu.forte-1"
SIMULATOR_TARGET = "simulator"
PROJECT_ID = "2237ddcc-2644-4dc1-b971-b3cbece475e1"
IONQ_BASE = "https://api.ionq.co/v0.3"

_TERMINAL_STATES = {"completed", "failed", "cancelled"}


def _api_key() -> str:
    key = os.environ.get("IONQ_API_KEY")
    if not key:
        raise RuntimeError("IONQ_API_KEY environment variable is not set")
    return key


def _headers() -> dict:
    return {"Authorization": f"apiKey {_api_key()}"}


def _build_native_circuit(input_bits: str, circuit_length: int) -> dict:
    """Build an IonQ native circuit definition for our CNOT litmus circuit."""
    ops = []
    if input_bits[0] == "1":
        ops.append({"gate": "x", "target": 0})
    if input_bits[1] == "1":
        ops.append({"gate": "x", "target": 1})
    for i in range(circuit_length):
        if i % 2 == 0:
            ops.append({"gate": "cnot", "control": 0, "target": 1})
        else:
            ops.append({"gate": "cnot", "control": 1, "target": 0})
    return {"qubits": 2, "circuit": ops}


def _lsb_key_to_bits(key: str) -> str:
    """Convert IonQ decimal result key to our 2-qubit bitstring (LSB convention)."""
    return format(int(key), "02b")[::-1]


def _raw_to_counts(raw_results: dict, shots: int) -> dict[str, int]:
    """Convert IonQ probability dict to shot counts keyed by our bitstring notation."""
    counts = {}
    for k, prob in raw_results.items():
        bitstring = _lsb_key_to_bits(k)
        count = round(prob * shots)
        if count > 0:
            counts[bitstring] = count
    return counts


def submit(
    n_circuits: int = 10, shots: int = 100, dry_run: bool = False, use_simulator: bool = False
) -> dict:
    """
    Submit circuits to IonQ Forte-1 and return a pending dict.
    The caller is responsible for saving this to pending/ionq_direct/<date>.json.
    """
    sampled_keys = sample_circuits(n_circuits)
    run_date = date.today().isoformat()
    submitted_at = datetime.now(UTC).isoformat()

    if dry_run:
        # Local simulation — no API calls, perfect results from REFERENCE_TABLE
        jobs = [
            {"job_id": f"dry-run-{i}", "input_bits": ib, "circuit_length": cl}
            for i, (ib, cl) in enumerate(sampled_keys)
        ]
        dry_results = []
        for job in jobs:
            ib, cl = job["input_bits"], job["circuit_length"]
            correct = REFERENCE_TABLE[(ib, cl)]
            dry_results.append({
                "run_date": run_date,
                "platform": PLATFORM,
                "backend": "LocalSim",
                "input_bits": ib,
                "circuit_length": cl,
                "shots": shots,
                "counts_json": json.dumps({correct: shots}),
                "success_probability": 1.0,
                "job_id": job["job_id"],
                "job_start_time": submitted_at,
                "job_end_time": submitted_at,
                "sdk_version": "",
                "notes": "dry_run",
            })
        return {
            "run_date": run_date,
            "platform": PLATFORM,
            "backend": "LocalSim",
            "shots": shots,
            "submitted_at": submitted_at,
            "dry_run": True,
            "jobs": jobs,
            "_dry_run_results": dry_results,
        }

    target = SIMULATOR_TARGET if use_simulator else TARGET
    backend = "simulator" if use_simulator else BACKEND
    hdrs = {**_headers(), "Content-Type": "application/json"}
    jobs = []

    for input_bits, circuit_length in sampled_keys:
        body = {
            "name": f"cnot_len{circuit_length}_{input_bits}",
            "target": target,
            "shots": shots,
            "project_id": PROJECT_ID,
            "circuit": _build_native_circuit(input_bits, circuit_length),
        }
        resp = requests.post(f"{IONQ_BASE}/jobs", headers=hdrs, json=body, timeout=30)
        resp.raise_for_status()
        job_id = resp.json()["id"]
        jobs.append({"job_id": job_id, "input_bits": input_bits, "circuit_length": circuit_length})
        print(f"    Submitted cnot_len{circuit_length}_{input_bits}: {job_id}")
        time.sleep(0.2)  # be gentle with the API

    print(f"  Submitted {len(jobs)} circuits to {target}")
    return {
        "run_date": run_date,
        "platform": PLATFORM,
        "backend": backend,
        "shots": shots,
        "submitted_at": submitted_at,
        "dry_run": False,
        "use_simulator": use_simulator,
        "jobs": jobs,
    }


def collect(pending: dict) -> list[dict] | None:
    """
    Check job status and collect results.

    Returns a list of result dicts if all jobs are complete.
    Returns None if any jobs are still running.
    Raises RuntimeError if any jobs failed or were cancelled.
    """
    if "_dry_run_results" in pending:
        return pending["_dry_run_results"]

    hdrs = _headers()
    shots = pending["shots"]
    results = []
    still_pending = []

    for job_meta in pending["jobs"]:
        job_id = job_meta["job_id"]
        resp = requests.get(f"{IONQ_BASE}/jobs/{job_id}", headers=hdrs, timeout=30)
        resp.raise_for_status()
        job = resp.json()
        status = job.get("status", "")

        if status in ("failed", "cancelled"):
            raise RuntimeError(f"Job {job_id} {status}")
        if status != "completed":
            still_pending.append(job_id)
            continue

        res_resp = requests.get(f"{IONQ_BASE}/jobs/{job_id}/results", headers=hdrs, timeout=30)
        res_resp.raise_for_status()
        raw = res_resp.json()

        input_bits = job_meta["input_bits"]
        circuit_length = job_meta["circuit_length"]
        counts = _raw_to_counts(raw, shots)
        correct = REFERENCE_TABLE[(input_bits, circuit_length)]
        success_prob = counts.get(correct, 0) / shots

        start_ts = job.get("start")
        end_ts = job.get("response")
        results.append({
            "run_date": pending["run_date"],
            "platform": pending["platform"],
            "backend": pending["backend"],
            "input_bits": input_bits,
            "circuit_length": circuit_length,
            "shots": shots,
            "counts_json": json.dumps(counts),
            "success_probability": round(success_prob, 4),
            "job_id": job_id,
            "job_start_time": datetime.fromtimestamp(start_ts, tz=UTC).isoformat() if start_ts else "",
            "job_end_time": datetime.fromtimestamp(end_ts, tz=UTC).isoformat() if end_ts else "",
            "sdk_version": "",
            "notes": _notes(pending),
        })
        time.sleep(0.1)

    if still_pending:
        print(f"  {len(still_pending)}/{len(pending['jobs'])} jobs still pending.")
        return None

    print(f"  All {len(results)} jobs complete.")
    return results


def _notes(pending: dict) -> str:
    if pending.get("dry_run"):
        return "dry_run"
    if pending.get("use_simulator"):
        return "simulator"
    return ""
