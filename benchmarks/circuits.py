"""
Platform-agnostic circuit definitions for the litmus-test benchmark.

The reference table (correct output per circuit) is deterministic and hardcoded —
no simulator call needed at run time.
"""

import itertools
import random

POSSIBLE_INPUT_BITS = ("00", "01", "10", "11")
POSSIBLE_CIRCUIT_LENGTHS = (1, 2, 3, 4, 5, 6)

# The correct output for each (input_bits, circuit_length) pair.
# Verified by simulation; deterministic for this circuit family.
#
#   00 | 00 00 00 00 00 00
#   01 | 01 11 10 10 11 01
#   10 | 11 01 01 11 10 10
#   11 | 10 10 11 01 01 11
REFERENCE_TABLE: dict[tuple[str, int], str] = {
    ("00", 1): "00", ("00", 2): "00", ("00", 3): "00",
    ("00", 4): "00", ("00", 5): "00", ("00", 6): "00",
    ("01", 1): "01", ("01", 2): "11", ("01", 3): "10",
    ("01", 4): "10", ("01", 5): "11", ("01", 6): "01",
    ("10", 1): "11", ("10", 2): "01", ("10", 3): "01",
    ("10", 4): "11", ("10", 5): "10", ("10", 6): "10",
    ("11", 1): "10", ("11", 2): "10", ("11", 3): "11",
    ("11", 4): "01", ("11", 5): "01", ("11", 6): "11",
}


def sample_circuits(n: int) -> list[tuple[str, int]]:
    """
    Stratified sample of n (input_bits, circuit_length) keys.
    Always includes at least one circuit from each of the 6 lengths,
    then fills the remainder randomly.
    """
    by_length: dict[int, list[tuple[str, int]]] = {n: [] for n in POSSIBLE_CIRCUIT_LENGTHS}
    for key in itertools.product(POSSIBLE_INPUT_BITS, POSSIBLE_CIRCUIT_LENGTHS):
        by_length[key[1]].append(key)

    sampled = [random.choice(by_length[length]) for length in POSSIBLE_CIRCUIT_LENGTHS]
    remaining = n - len(sampled)
    if remaining > 0:
        all_keys = list(itertools.product(POSSIBLE_INPUT_BITS, POSSIBLE_CIRCUIT_LENGTHS))
        sampled += random.choices(all_keys, k=remaining)
    return sampled[:n]


def build_circuit_braket(input_bits: str, circuit_length: int):
    """Build the CNOT litmus circuit using the AWS Braket SDK."""
    from braket.circuits import Circuit

    c = Circuit()
    if input_bits[0] == "1":
        c.x(0)
    if input_bits[1] == "1":
        c.x(1)
    for idx in range(circuit_length):
        if idx % 2 == 0:
            c.cnot(0, 1)
        else:
            c.cnot(1, 0)
    return c


def build_circuit_qiskit(input_bits: str, circuit_length: int):
    """Build the CNOT litmus circuit using Qiskit."""
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(2, name=f"cnot_len{circuit_length}_{input_bits}")
    if input_bits[0] == "1":
        qc.x(0)
    if input_bits[1] == "1":
        qc.x(1)
    for idx in range(circuit_length):
        if idx % 2 == 0:
            qc.cx(0, 1)
        else:
            qc.cx(1, 0)
    return qc
