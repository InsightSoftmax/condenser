"""
Tests for circuit generation, sampling, and the reference table.
No QPU or cloud calls are made here.
"""

import itertools

from benchmarks.circuits import (
    POSSIBLE_CIRCUIT_LENGTHS,
    POSSIBLE_INPUT_BITS,
    REFERENCE_TABLE,
    build_circuit_braket,
    build_circuit_qiskit,
    sample_circuits,
)

# --- Reference table ---

def test_reference_table_completeness():
    """All 24 (input_bits, length) keys must be present."""
    for key in itertools.product(POSSIBLE_INPUT_BITS, POSSIBLE_CIRCUIT_LENGTHS):
        assert key in REFERENCE_TABLE, f"Missing key: {key}"


def test_reference_table_valid_outputs():
    """All reference outputs must be valid 2-qubit bitstrings."""
    valid = {"00", "01", "10", "11"}
    for key, output in REFERENCE_TABLE.items():
        assert output in valid, f"Invalid output {output!r} for key {key}"


def test_reference_table_identity_for_00_input():
    """Input 00 through any CNOT sequence should always return 00."""
    for length in POSSIBLE_CIRCUIT_LENGTHS:
        assert REFERENCE_TABLE[("00", length)] == "00"


# --- Circuit builders ---

def test_braket_circuit_qubit_count():
    for input_bits, length in itertools.product(POSSIBLE_INPUT_BITS, POSSIBLE_CIRCUIT_LENGTHS):
        circuit = build_circuit_braket(input_bits, length)
        assert circuit.qubit_count == 2


def test_qiskit_circuit_qubit_count():
    for input_bits, length in itertools.product(POSSIBLE_INPUT_BITS, POSSIBLE_CIRCUIT_LENGTHS):
        circuit = build_circuit_qiskit(input_bits, length)
        assert circuit.num_qubits == 2


def test_braket_circuit_not_none():
    for key in itertools.product(POSSIBLE_INPUT_BITS, POSSIBLE_CIRCUIT_LENGTHS):
        assert build_circuit_braket(*key) is not None


def test_qiskit_circuit_not_none():
    for key in itertools.product(POSSIBLE_INPUT_BITS, POSSIBLE_CIRCUIT_LENGTHS):
        assert build_circuit_qiskit(*key) is not None


# --- Circuit gate counts ---

def test_qiskit_circuit_cnot_count_matches_length():
    """Qiskit circuit must contain exactly circuit_length CX (CNOT) gates."""
    for input_bits, length in itertools.product(POSSIBLE_INPUT_BITS, POSSIBLE_CIRCUIT_LENGTHS):
        circuit = build_circuit_qiskit(input_bits, length)
        cx_count = sum(1 for g in circuit.data if g.operation.name == "cx")
        assert cx_count == length, f"{input_bits=} {length=}: expected {length} CX, got {cx_count}"


def test_braket_circuit_cnot_count_matches_length():
    """Braket circuit must contain exactly circuit_length CNot gates."""
    for input_bits, length in itertools.product(POSSIBLE_INPUT_BITS, POSSIBLE_CIRCUIT_LENGTHS):
        circuit = build_circuit_braket(input_bits, length)
        cnot_count = sum(1 for i in circuit.instructions if i.operator.name == "CNot")
        assert cnot_count == length, f"{input_bits=} {length=}: expected {length} CNot, got {cnot_count}"


def test_qiskit_circuit_input_state_x_gates():
    """Qiskit circuit must have an X gate on qubit k for each '1' bit at position k."""
    for input_bits in POSSIBLE_INPUT_BITS:
        circuit = build_circuit_qiskit(input_bits, 1)
        x_targets = {g.qubits[0]._index for g in circuit.data if g.operation.name == "x"}
        expected = {i for i, b in enumerate(input_bits) if b == "1"}
        assert x_targets == expected, f"{input_bits=}: expected X on qubits {expected}, got {x_targets}"


# --- Sampling ---

def test_sample_circuits_count():
    for n in (6, 10, 15, 24):
        assert len(sample_circuits(n)) == n


def test_sample_circuits_covers_all_lengths():
    """With n >= 6, all circuit lengths must appear at least once."""
    sample = sample_circuits(10)
    lengths_present = {length for _, length in sample}
    assert lengths_present == set(POSSIBLE_CIRCUIT_LENGTHS)


def test_sample_circuits_valid_keys():
    valid = set(itertools.product(POSSIBLE_INPUT_BITS, POSSIBLE_CIRCUIT_LENGTHS))
    for key in sample_circuits(10):
        assert key in valid
