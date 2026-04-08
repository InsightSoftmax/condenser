"""
Tests for the Observable Framework data loaders in dashboard/src/data/.

Each loader is a standalone Python script that writes JSON to stdout.
We run them via subprocess and validate the output shape and values.
"""
import json
import subprocess
import sys
from pathlib import Path

LOADER_DIR = Path(__file__).parent.parent / "dashboard" / "src" / "data"


def run_loader(filename: str) -> dict | list:
    result = subprocess.run(
        [sys.executable, str(LOADER_DIR / filename)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# rigetti.json.py
# ---------------------------------------------------------------------------

def test_rigetti_loader_keys():
    data = run_loader("rigetti.json.py")
    assert set(data.keys()) >= {"platform", "backend", "runs", "circuits", "by_length", "by_input"}


def test_rigetti_has_data():
    data = run_loader("rigetti.json.py")
    assert len(data["runs"]) > 0
    assert len(data["circuits"]) > 0


def test_rigetti_run_schema():
    data = run_loader("rigetti.json.py")
    for run in data["runs"]:
        assert "run_date" in run
        assert "mean_success" in run
        assert "std_success" in run
        assert "n_circuits" in run
        assert 0.0 <= run["mean_success"] <= 1.0
        assert run["std_success"] >= 0.0


def test_rigetti_excludes_simulator_rows():
    """Simulator/dry-run rows must not appear in loader output."""
    data = run_loader("rigetti.json.py")
    for circuit in data["circuits"]:
        assert circuit.get("notes", "") == "" or "notes" not in circuit


def test_rigetti_by_length_covers_all_depths():
    data = run_loader("rigetti.json.py")
    lengths = {d["length"] for d in data["by_length"]}
    assert lengths == {1, 2, 3, 4, 5, 6}


def test_rigetti_by_input_covers_all_states():
    data = run_loader("rigetti.json.py")
    states = {d["input_bits"] for d in data["by_input"]}
    assert states == {"00", "01", "10", "11"}


def test_rigetti_success_range():
    data = run_loader("rigetti.json.py")
    for row in data["by_length"]:
        assert 0.0 <= row["mean_success"] <= 1.0
    for row in data["by_input"]:
        assert 0.0 <= row["mean_success"] <= 1.0


# ---------------------------------------------------------------------------
# ionq.json.py
# ---------------------------------------------------------------------------

def test_ionq_loader_keys():
    data = run_loader("ionq.json.py")
    assert set(data.keys()) >= {"platform", "backend", "runs", "circuits", "by_length", "by_input"}


def test_ionq_aria_only():
    """IonQ loader must filter to Aria-1 only (not Harmony)."""
    data = run_loader("ionq.json.py")
    assert data["backend"] == "Aria-1"
    assert len(data["runs"]) > 0


def test_ionq_run_schema():
    data = run_loader("ionq.json.py")
    for run in data["runs"]:
        assert "run_date" in run
        assert 0.0 <= run["mean_success"] <= 1.0


# ---------------------------------------------------------------------------
# summary.json.py
# ---------------------------------------------------------------------------

def test_summary_is_list():
    data = run_loader("summary.json.py")
    assert isinstance(data, list)


def test_summary_has_all_platforms():
    data = run_loader("summary.json.py")
    platforms = {p["platform"] for p in data}
    assert {"rigetti", "ionq", "aqt"} <= platforms


def test_summary_rigetti_populated():
    data = run_loader("summary.json.py")
    rigetti = next(p for p in data if p["platform"] == "rigetti")
    assert rigetti["n_runs"] > 0
    assert rigetti["latest_success"] is not None
    assert 0.0 <= rigetti["latest_success"] <= 1.0
    assert len(rigetti["sparkline"]) > 0


def test_summary_sparkline_schema():
    data = run_loader("summary.json.py")
    for platform in data:
        for point in platform["sparkline"]:
            assert "date" in point
            assert "value" in point
            assert 0.0 <= point["value"] <= 1.0


def test_summary_aqt_no_data_yet():
    """AQT has no real QPU runs yet — loader should return empty lists gracefully."""
    data = run_loader("summary.json.py")
    aqt = next(p for p in data if p["platform"] == "aqt")
    assert aqt["sparkline"] == []
