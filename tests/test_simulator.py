"""
End-to-end simulator tests for all platform modules.

These tests run the full submit → collect pipeline using local simulators
(Braket LocalSimulator, AQT offline_simulator_no_noise). No QPU credits
are consumed and no cloud credentials are required.

Each test validates:
  - submit() returns a well-formed pending dict
  - collect() returns results matching the CSV schema
  - success_probability is in [0, 1]
  - notes == "dry_run"
"""

import json

RESULT_SCHEMA = {
    "run_date", "platform", "backend", "input_bits", "circuit_length",
    "shots", "counts_json", "success_probability", "job_id",
    "job_start_time", "job_end_time", "sdk_version", "notes",
}

N_CIRCUITS = 2   # small for speed
SHOTS = 20


def _validate_results(results: list[dict], n_circuits: int, shots: int) -> None:
    assert isinstance(results, list)
    assert len(results) == n_circuits
    for r in results:
        missing = RESULT_SCHEMA - r.keys()
        assert not missing, f"Missing fields: {missing}"
        assert r["notes"] == "dry_run"
        assert 0.0 <= r["success_probability"] <= 1.0
        counts = json.loads(r["counts_json"])
        assert sum(counts.values()) == shots
        assert r["input_bits"] in ("00", "01", "10", "11")
        assert 1 <= r["circuit_length"] <= 6


class TestRigettiSimulator:
    def test_submit_returns_pending_dict(self):
        from benchmarks import rigetti_braket
        pending = rigetti_braket.submit(n_circuits=N_CIRCUITS, shots=SHOTS, dry_run=True)
        assert pending["platform"] == "rigetti"
        assert pending["backend"] == "LocalSimulator"
        assert pending["dry_run"] is True
        assert len(pending["jobs"]) == N_CIRCUITS

    def test_collect_returns_results(self):
        from benchmarks import rigetti_braket
        pending = rigetti_braket.submit(n_circuits=N_CIRCUITS, shots=SHOTS, dry_run=True)
        results = rigetti_braket.collect(pending)
        _validate_results(results, N_CIRCUITS, SHOTS)

    def test_full_pipeline_via_json_round_trip(self):
        """Pending dict must survive JSON serialization (as it does when saved to disk)."""
        from benchmarks import rigetti_braket
        pending = rigetti_braket.submit(n_circuits=N_CIRCUITS, shots=SHOTS, dry_run=True)
        pending_reloaded = json.loads(json.dumps(pending, default=str))
        results = rigetti_braket.collect(pending_reloaded)
        _validate_results(results, N_CIRCUITS, SHOTS)


class TestIonQSimulator:
    def test_submit_returns_pending_dict(self):
        from benchmarks import ionq_braket
        pending = ionq_braket.submit(n_circuits=N_CIRCUITS, shots=SHOTS, dry_run=True)
        assert pending["platform"] == "ionq"
        assert pending["backend"] == "LocalSimulator"
        assert pending["dry_run"] is True
        assert len(pending["jobs"]) == N_CIRCUITS

    def test_collect_returns_results(self):
        from benchmarks import ionq_braket
        pending = ionq_braket.submit(n_circuits=N_CIRCUITS, shots=SHOTS, dry_run=True)
        results = ionq_braket.collect(pending)
        _validate_results(results, N_CIRCUITS, SHOTS)

    def test_full_pipeline_via_json_round_trip(self):
        from benchmarks import ionq_braket
        pending = ionq_braket.submit(n_circuits=N_CIRCUITS, shots=SHOTS, dry_run=True)
        pending_reloaded = json.loads(json.dumps(pending, default=str))
        results = ionq_braket.collect(pending_reloaded)
        _validate_results(results, N_CIRCUITS, SHOTS)


class TestIBMSimulator:
    def test_submit_returns_pending_dict(self):
        from benchmarks import ibm_qiskit
        pending = ibm_qiskit.submit(n_circuits=N_CIRCUITS, shots=SHOTS, dry_run=True)
        assert pending["platform"] == "ibm"
        assert pending["backend"] == "StatevectorSimulator"
        assert pending["dry_run"] is True
        assert len(pending["jobs"]) == N_CIRCUITS

    def test_collect_returns_results(self):
        from benchmarks import ibm_qiskit
        pending = ibm_qiskit.submit(n_circuits=N_CIRCUITS, shots=SHOTS, dry_run=True)
        results = ibm_qiskit.collect(pending)
        _validate_results(results, N_CIRCUITS, SHOTS)

    def test_full_pipeline_via_json_round_trip(self):
        """Pending dict must survive JSON serialization (as it does when saved to disk)."""
        from benchmarks import ibm_qiskit
        pending = ibm_qiskit.submit(n_circuits=N_CIRCUITS, shots=SHOTS, dry_run=True)
        pending_reloaded = json.loads(json.dumps(pending, default=str))
        results = ibm_qiskit.collect(pending_reloaded)
        _validate_results(results, N_CIRCUITS, SHOTS)


class TestAQTSimulator:
    def test_submit_returns_pending_dict(self):
        from benchmarks import aqt_qiskit
        pending = aqt_qiskit.submit(n_circuits=N_CIRCUITS, shots=SHOTS, dry_run=True)
        assert pending["platform"] == "aqt"
        assert pending["backend"] == "offline_simulator_no_noise"
        assert pending["dry_run"] is True
        assert len(pending["jobs"]) == N_CIRCUITS

    def test_collect_returns_results(self):
        from benchmarks import aqt_qiskit
        pending = aqt_qiskit.submit(n_circuits=N_CIRCUITS, shots=SHOTS, dry_run=True)
        results = aqt_qiskit.collect(pending)
        _validate_results(results, N_CIRCUITS, SHOTS)

    def test_full_pipeline_via_json_round_trip(self):
        from benchmarks import aqt_qiskit
        pending = aqt_qiskit.submit(n_circuits=N_CIRCUITS, shots=SHOTS, dry_run=True)
        pending_reloaded = json.loads(json.dumps(pending, default=str))
        results = aqt_qiskit.collect(pending_reloaded)
        _validate_results(results, N_CIRCUITS, SHOTS)
