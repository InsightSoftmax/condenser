"""
Tests for scripts/submit_benchmark.py and scripts/collect_results.py.

Uses dry-run mode throughout — no cloud credentials or QPU credits needed.
Uses tmp_path for filesystem isolation.
"""
import csv
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).parent.parent
SCRIPTS = REPO_ROOT / "scripts"
ENV = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}


def run_script(name: str, args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args],
        capture_output=True, text=True, cwd=cwd, env=ENV,
    )


# ---------------------------------------------------------------------------
# append_results — unit tests
# ---------------------------------------------------------------------------

@pytest.fixture
def append_results(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Re-import so the cwd-relative paths inside the function resolve to tmp_path
    import importlib, sys
    sys.path.insert(0, str(REPO_ROOT))
    import scripts.collect_results as cr
    importlib.reload(cr)
    return cr.append_results


SAMPLE_ROW = {
    "run_date": "2026-04-09", "platform": "rigetti", "backend": "TestBackend",
    "input_bits": "00", "circuit_length": 1, "shots": 10,
    "counts_json": '{"00": 10}', "success_probability": 1.0,
    "job_id": "test-id", "job_start_time": "", "job_end_time": "",
    "sdk_version": "1.0", "notes": "dry_run",
}


def test_append_results_creates_csv_with_header(append_results, tmp_path):
    append_results("rigetti", [SAMPLE_ROW])
    csv_path = tmp_path / "data" / "rigetti" / "results.csv"
    assert csv_path.exists()
    rows = list(csv.DictReader(csv_path.open()))
    assert len(rows) == 1
    assert rows[0]["platform"] == "rigetti"
    assert rows[0]["run_date"] == "2026-04-09"


def test_append_results_no_double_header(append_results, tmp_path):
    """Calling append_results twice must not write the header as a data row."""
    append_results("rigetti", [SAMPLE_ROW])
    append_results("rigetti", [{**SAMPLE_ROW, "job_id": "second"}])
    csv_path = tmp_path / "data" / "rigetti" / "results.csv"
    rows = list(csv.DictReader(csv_path.open()))
    assert len(rows) == 2


def test_append_results_creates_parent_directory(append_results, tmp_path):
    """Parent directories should be created automatically."""
    append_results("newplatform", [SAMPLE_ROW])
    assert (tmp_path / "data" / "newplatform" / "results.csv").exists()


def test_append_results_missing_fields_written_as_empty(append_results, tmp_path):
    """Fields absent from the result dict should be written as empty strings."""
    sparse_row = {"run_date": "2026-04-09", "platform": "rigetti",
                  "success_probability": 0.9}
    append_results("rigetti", [sparse_row])
    rows = list(csv.DictReader((tmp_path / "data" / "rigetti" / "results.csv").open()))
    assert rows[0]["job_id"] == ""
    assert rows[0]["notes"] == ""


# ---------------------------------------------------------------------------
# submit_benchmark.py integration
# ---------------------------------------------------------------------------

@pytest.fixture
def submitted(tmp_path):
    result = run_script("submit_benchmark.py", ["--dry-run"], tmp_path)
    assert result.returncode == 0, result.stderr
    return tmp_path


def test_submit_creates_pending_files(submitted):
    pending = list((submitted / "pending").glob("*/*.json"))
    assert len(pending) >= 1


def test_pending_file_top_level_schema(submitted):
    for f in (submitted / "pending").glob("*/*.json"):
        data = json.loads(f.read_text())
        for key in ("platform", "backend", "run_date", "shots", "dry_run", "jobs"):
            assert key in data, f"{key} missing from {f.name}"
        assert data["dry_run"] is True


def test_pending_file_jobs_schema(submitted):
    for f in (submitted / "pending").glob("*/*.json"):
        data = json.loads(f.read_text())
        for job in data["jobs"]:
            assert "job_id" in job
            assert job["input_bits"] in ("00", "01", "10", "11")
            assert 1 <= job["circuit_length"] <= 6


def test_pending_file_placed_under_platform_directory(submitted):
    for f in (submitted / "pending").glob("*/*.json"):
        data = json.loads(f.read_text())
        # The directory name is the module name (e.g. rigetti_braket);
        # the platform key inside must match known platforms.
        assert data["platform"] in ("rigetti", "aqt", "ionq", "ibm")


# ---------------------------------------------------------------------------
# collect_results.py integration
# ---------------------------------------------------------------------------

def test_collect_with_no_pending_dir_exits_cleanly(tmp_path):
    result = run_script("collect_results.py", [], tmp_path)
    assert result.returncode == 0
    assert "Nothing to collect" in result.stdout or "No pending" in result.stdout


def test_collect_writes_csv_and_removes_pending_files(submitted):
    result = run_script("collect_results.py", [], submitted)
    assert result.returncode == 0, result.stderr
    # All pending files should be gone
    remaining = list((submitted / "pending").glob("*/*.json"))
    assert remaining == []
    # At least one CSV should have been written
    csvs = list((submitted / "data").glob("*/results.csv"))
    assert len(csvs) >= 1


def test_collected_csv_matches_schema(submitted):
    run_script("collect_results.py", [], submitted)
    expected_fields = {
        "run_date", "platform", "backend", "input_bits", "circuit_length",
        "shots", "counts_json", "success_probability", "job_id",
        "job_start_time", "job_end_time", "sdk_version", "notes",
    }
    for csv_path in (submitted / "data").glob("*/results.csv"):
        rows = list(csv.DictReader(csv_path.open()))
        assert len(rows) > 0
        assert set(rows[0].keys()) == expected_fields


def test_collected_rows_are_dry_run(submitted):
    run_script("collect_results.py", [], submitted)
    for csv_path in (submitted / "data").glob("*/results.csv"):
        for row in csv.DictReader(csv_path.open()):
            assert row["notes"] == "dry_run"
            assert 0.0 <= float(row["success_probability"]) <= 1.0


def test_collect_still_waiting_keeps_pending_file(tmp_path):
    """If collect() returns None, the pending file must not be removed."""
    # Create a minimal pending file for rigetti_braket
    pending_dir = tmp_path / "pending" / "rigetti_braket"
    pending_dir.mkdir(parents=True)
    pending_file = pending_dir / "2026-04-09.json"
    pending_file.write_text(json.dumps({
        "run_date": "2026-04-09", "platform": "rigetti", "backend": "Ankaa-3",
        "dry_run": False, "shots": 100, "jobs": [{"job_id": "fake-id",
        "input_bits": "00", "circuit_length": 1}],
    }))

    # Patch rigetti_braket.collect to return None (still waiting)
    with patch.dict("sys.modules", {}):
        import importlib
        import scripts.collect_results as cr
        importlib.reload(cr)

        import benchmarks.rigetti_braket as rb
        with patch.object(rb, "collect", return_value=None):
            os.chdir(tmp_path)
            with patch("builtins.__import__", side_effect=lambda name, *a, **kw:
                       rb if name == "benchmarks.rigetti_braket" else __import__(name, *a, **kw)):
                cr.main()

    assert pending_file.exists(), "Pending file should not be removed when still waiting"


def test_collect_runtime_error_removes_pending_file(tmp_path):
    """If collect() raises RuntimeError, the pending file must be removed."""
    pending_dir = tmp_path / "pending" / "rigetti_braket"
    pending_dir.mkdir(parents=True)
    pending_file = pending_dir / "2026-04-09.json"
    pending_file.write_text(json.dumps({
        "run_date": "2026-04-09", "platform": "rigetti", "backend": "Ankaa-3",
        "dry_run": False, "shots": 100, "jobs": [{"job_id": "fake-id",
        "input_bits": "00", "circuit_length": 1}],
    }))

    import importlib
    import scripts.collect_results as cr
    importlib.reload(cr)

    import benchmarks.rigetti_braket as rb
    with patch.object(rb, "collect", side_effect=RuntimeError("job failed")):
        os.chdir(tmp_path)
        with patch("builtins.__import__", side_effect=lambda name, *a, **kw:
                   rb if name == "benchmarks.rigetti_braket" else __import__(name, *a, **kw)):
            cr.main()

    assert not pending_file.exists(), "Pending file should be removed on RuntimeError"
