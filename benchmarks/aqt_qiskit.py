"""
AQT benchmark via Qiskit + qiskit-aqt-provider.

Authentication: AQT_API_KEY environment variable (GitHub secret).
SDK: qiskit, qiskit-aqt-provider

Key quirk: AQT returns bitstrings in reversed qubit order relative to the rest of
this project. Counts keys are flipped with [::-1] before comparing to REFERENCE_TABLE.
"""

import importlib.metadata
import json
import os
import tempfile
from datetime import UTC, date, datetime
from pathlib import Path

from benchmarks.circuits import REFERENCE_TABLE, build_circuit_qiskit, sample_circuits

PLATFORM = "aqt"
HARDWARE_BACKEND = "ibex"
OFFLINE_SIMULATOR = "offline_simulator_no_noise"
ONLINE_SIMULATOR = "simulator_noise"


def _get_provider():
    from qiskit_aqt_provider import AQTProvider
    return AQTProvider(os.environ.get("AQT_API_KEY", ""))


def submit(
    n_circuits: int = 10, shots: int = 100, dry_run: bool = False, use_simulator: bool = False
) -> dict:
    """Submit circuits and return a pending dict."""
    from qiskit import transpile

    try:
        sdk_version = importlib.metadata.version("qiskit-aqt-provider")
    except importlib.metadata.PackageNotFoundError:
        sdk_version = importlib.metadata.version("qiskit")

    provider = _get_provider()
    if dry_run:
        backend_name = OFFLINE_SIMULATOR
    elif use_simulator:
        backend_name = ONLINE_SIMULATOR
    else:
        backend_name = HARDWARE_BACKEND
    backend = provider.get_backend(backend_name)

    sampled_keys = sample_circuits(n_circuits)

    raw_circuits = []
    for input_bits, length in sampled_keys:
        qc = build_circuit_qiskit(input_bits, length)
        qc.measure_all()
        raw_circuits.append(qc)

    backend.options.update_options(with_progress_bar=False)

    print(f"  Transpiling {len(raw_circuits)} circuits to AQT native gates...")
    transpiled = transpile(raw_circuits, backend=backend, optimization_level=3)

    print(f"  Submitting {len(transpiled)} circuits to {backend_name}...")
    jobs = [backend.run(qc, shots=shots) for qc in transpiled]

    pending = {
        "run_date": date.today().isoformat(),
        "platform": PLATFORM,
        "backend": backend_name,
        "sdk_version": sdk_version,
        "shots": shots,
        "submitted_at": datetime.now(UTC).isoformat(),
        "dry_run": dry_run,
        "use_simulator": use_simulator,
        "jobs": [
            {"job_id": job.job_id(), "input_bits": input_bits, "circuit_length": circuit_length}
            for job, (input_bits, circuit_length) in zip(jobs, sampled_keys)
        ],
    }

    if dry_run:
        # Offline simulator runs synchronously. Collect results now so collect() can return
        # them without needing backend.retrieve_job() on an in-memory job after reload.
        pending["_dry_run_results"] = _collect_jobs(pending["jobs"], jobs, pending)
    else:
        # qiskit-aqt-provider has no retrieve_job(). Persist each job's circuit + options
        # data into the pending file so collect() can reconstruct the AQTJob object.
        for job, job_meta in zip(jobs, pending["jobs"]):
            with tempfile.TemporaryDirectory() as store_dir:
                persist_path = job.persist(store_path=Path(store_dir))
                job_meta["_aqt_job_data"] = persist_path.read_text()

    return pending


def _collect_jobs(jobs_meta: list, jobs: list, pending: dict) -> list[dict]:
    """Build result dicts from already-completed job objects (used for dry runs)."""
    results = []
    for job_meta, job in zip(jobs_meta, jobs):
        counts_raw = job.result().get_counts()
        counts = {bs[::-1]: count for bs, count in counts_raw.items()}
        correct = REFERENCE_TABLE[(job_meta["input_bits"], job_meta["circuit_length"])]
        success_prob = counts.get(correct, 0) / pending["shots"]
        results.append({
            "run_date": pending["run_date"],
            "platform": pending["platform"],
            "backend": pending["backend"],
            "input_bits": job_meta["input_bits"],
            "circuit_length": job_meta["circuit_length"],
            "shots": pending["shots"],
            "counts_json": json.dumps(counts),
            "success_probability": round(success_prob, 4),
            "job_id": job_meta["job_id"],
            "job_start_time": None,
            "job_end_time": None,
            "sdk_version": pending["sdk_version"],
            "notes": _notes(pending),
        })
    return results


def _notes(pending: dict) -> str:
    if pending.get("dry_run"):
        return "dry_run"
    if pending.get("use_simulator"):
        return "simulator"
    return ""


def collect(pending: dict) -> list[dict] | None:
    """
    Check the status of pending jobs.

    Returns results if all jobs are done, None if still waiting.
    Raises RuntimeError if any jobs failed or were cancelled.
    """
    if "_dry_run_results" in pending:
        return pending["_dry_run_results"]

    from qiskit.providers import JobStatus
    from qiskit_aqt_provider.aqt_job import AQTJob

    api_key = os.environ.get("AQT_API_KEY", "")
    jobs = pending["jobs"]

    retrieved = []
    for job in jobs:
        with tempfile.TemporaryDirectory() as store_dir:
            store_path = Path(store_dir)
            (store_path / job["job_id"]).write_text(job["_aqt_job_data"])
            retrieved.append(
                AQTJob.restore(job["job_id"], access_token=api_key, store_path=store_path)
            )

    statuses = [job.status() for job in retrieved]

    failed = [
        job["job_id"] for job, status in zip(jobs, statuses)
        if status in (JobStatus.ERROR, JobStatus.CANCELLED)
    ]
    if failed:
        raise RuntimeError(f"Jobs failed/cancelled: {failed}")

    still_pending = [
        job["job_id"] for job, status in zip(jobs, statuses)
        if status not in (JobStatus.DONE, JobStatus.ERROR, JobStatus.CANCELLED)
    ]
    if still_pending:
        print(f"  {len(still_pending)}/{len(jobs)} jobs still pending.")
        return None

    print(f"  All {len(jobs)} jobs complete. Collecting results...")
    results = []
    for job_meta, job in zip(jobs, retrieved):
        counts_raw = job.result().get_counts()
        # AQT returns bitstrings in reversed qubit order — flip before comparing.
        counts = {bitstr[::-1]: count for bitstr, count in counts_raw.items()}

        correct = REFERENCE_TABLE[(job_meta["input_bits"], job_meta["circuit_length"])]
        success_prob = counts.get(correct, 0) / pending["shots"]

        results.append({
            "run_date": pending["run_date"],
            "platform": pending["platform"],
            "backend": pending["backend"],
            "input_bits": job_meta["input_bits"],
            "circuit_length": job_meta["circuit_length"],
            "shots": pending["shots"],
            "counts_json": json.dumps(counts),
            "success_probability": round(success_prob, 4),
            "job_id": job_meta["job_id"],
            "job_start_time": None,  # not exposed by qiskit-aqt-provider
            "job_end_time": None,
            "sdk_version": pending["sdk_version"],
            "notes": _notes(pending),
        })
    return results
