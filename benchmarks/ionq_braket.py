"""
IonQ benchmark via AWS Braket.

Authentication: OIDC-assumed IAM role (set up in infra/). No explicit credentials needed.
SDK: amazon-braket-sdk
Backend: IonQ Aria-1

IonQ queues can be measured in days. This module uses a two-stage approach:
  - submit()  → submit jobs, return a pending dict to be saved to disk
  - collect() → check job status, return results if all done, None if still waiting
"""

import importlib.metadata
import json
import os
from datetime import UTC, date, datetime

from benchmarks.circuits import REFERENCE_TABLE, build_circuit_braket, sample_circuits

PLATFORM = "ionq"
BACKEND_ARN = "arn:aws:braket:us-east-1::device/qpu/ionq/Aria-1"
SV1_ARN = "arn:aws:braket:::device/quantum-simulator/amazon/sv1"

S3_PREFIX = "condenser-results"

_TERMINAL_STATES = {"COMPLETED", "FAILED", "CANCELLED"}


def _s3_folder() -> tuple[str, str]:
    bucket = os.environ.get("BRAKET_RESULTS_BUCKET")
    if not bucket:
        raise RuntimeError("BRAKET_RESULTS_BUCKET environment variable is not set")
    return (bucket, S3_PREFIX)


def submit(
    n_circuits: int = 10, shots: int = 100, dry_run: bool = False, use_simulator: bool = False
) -> dict:
    """
    Submit circuits and return a pending dict.
    The caller is responsible for saving this to pending/ionq/<date>.json.
    """
    from braket.aws import AwsDevice
    from braket.devices import LocalSimulator

    sdk_version = importlib.metadata.version("amazon-braket-sdk")

    if dry_run:
        device = LocalSimulator()
        backend = "LocalSimulator"
        s3_folder = ("dry-run-bucket", S3_PREFIX)
    elif use_simulator:
        import boto3
        from braket.aws import AwsSession
        device = AwsDevice(SV1_ARN, aws_session=AwsSession(boto3.Session(region_name="us-east-1")))
        backend = "SV1"
        s3_folder = _s3_folder()
    else:
        device = AwsDevice(BACKEND_ARN)
        backend = device.name
        s3_folder = _s3_folder()

    sampled_keys = sample_circuits(n_circuits)
    circuits = [build_circuit_braket(input_bits, length) for input_bits, length in sampled_keys]

    print(f"  Submitting {len(circuits)} circuits to {backend}...")
    if dry_run:
        tasks = [device.run(circuit, shots=shots) for circuit in circuits]
    else:
        tasks = [device.run(circuit, s3_folder, shots=shots) for circuit in circuits]

    pending = {
        "run_date": date.today().isoformat(),
        "platform": PLATFORM,
        "backend": backend,
        "sdk_version": sdk_version,
        "shots": shots,
        "submitted_at": datetime.now(UTC).isoformat(),
        "dry_run": dry_run,
        "use_simulator": use_simulator,
        "jobs": [
            {"job_id": task.id, "input_bits": input_bits, "circuit_length": circuit_length}
            for task, (input_bits, circuit_length) in zip(tasks, sampled_keys)
        ],
    }

    if dry_run:
        pending["_dry_run_results"] = _collect_tasks(pending["jobs"], tasks, pending)

    return pending


def _collect_tasks(jobs_meta: list, tasks: list, pending: dict) -> list[dict]:
    """Build result dicts from already-completed task objects (used for dry runs)."""
    results = []
    for job_meta, task in zip(jobs_meta, tasks):
        result = task.result()
        counts = dict(result.measurement_counts)
        correct = REFERENCE_TABLE[(job_meta["input_bits"], job_meta["circuit_length"])]
        success_prob = counts.get(correct, 0) / pending["shots"]
        metadata = result.task_metadata
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
            "job_start_time": getattr(metadata, "createdAt", None),
            "job_end_time": getattr(metadata, "endedAt", None),
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

    Returns a list of result dicts (matching the CSV schema) if all jobs are done.
    Returns None if any jobs are still queued or running.
    Raises RuntimeError if any jobs failed or were cancelled.
    """
    if "_dry_run_results" in pending:
        return pending["_dry_run_results"]

    from braket.aws import AwsQuantumTask

    jobs = pending["jobs"]
    tasks = [AwsQuantumTask(job["job_id"]) for job in jobs]
    states = [task.state() for task in tasks]

    failed = [job["job_id"] for job, state in zip(jobs, states) if state in ("FAILED", "CANCELLED")]
    if failed:
        raise RuntimeError(f"Jobs failed/cancelled: {failed}")

    still_pending = [
        job["job_id"] for job, state in zip(jobs, states) if state not in _TERMINAL_STATES
    ]
    if still_pending:
        print(f"  {len(still_pending)}/{len(jobs)} jobs still pending.")
        return None

    print(f"  All {len(jobs)} jobs complete. Collecting results...")
    results = []
    for job_meta, task in zip(jobs, tasks):
        result = task.result()
        counts = dict(result.measurement_counts)
        correct = REFERENCE_TABLE[(job_meta["input_bits"], job_meta["circuit_length"])]
        success_prob = counts.get(correct, 0) / pending["shots"]

        metadata = result.task_metadata
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
            "job_start_time": getattr(metadata, "createdAt", None),
            "job_end_time": getattr(metadata, "endedAt", None),
            "sdk_version": pending["sdk_version"],
            "notes": _notes(pending),
        })
    return results
