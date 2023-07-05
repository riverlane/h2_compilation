# (c) Copyright Riverlane 2022-2023. All rights reserved.

"""
Simulates lattice surgery operations via qiskit, specifically using
joint ZZ and XX measurements.
"""
import argparse
import os

from qiskit import QuantumCircuit
from qiskit.providers.aer import QasmSimulator

from logical_circuit.clifford_plus_t import print_counts


def get_total_counts(qc, counts):
    """Sum over unwanted classical registers to extract the desired
    measurement results, which should be 3 bits.

    This assumes that either:
    - The 3 desired bits were measured into a single classical
      register of size 3, called c0.
    - The 3 desired bits were measured into three classical
      registers of size 1 each, called c0, c1 and c2.

    Parameters
    ----------
    qc : qiskit QuantumCircuit
        The circuit containing the classical registers.
    counts : dict
        The dictionary of measurement results. Keys are measurement
        results as strings, including all classical registers. Values
        are the associated counts.

    Returns
    -------
    totals : dict
       A dictionary as for counts above, but with the unwanted
       classical register results summed over, so that each key is
       a string consisting of 3 bits.
    """
    names = [x.name for x in qc.cregs]
    sizes = [x.size for x in qc.cregs]
    # The width of the string of results, including the space after
    widths = [x + 1 for x in sizes]

    c0_ind = names.index("c0")
    c0_size = sizes[c0_ind]

    c1_and_c2_exist = "c1" in names and "c2" in names

    if c0_size == 3:
        bit_0_ind = sum(widths[:c0_ind])
        bit_1_ind = bit_0_ind + 1
        bit_2_ind = bit_0_ind + 2
    elif c0_size == 1 and c1_and_c2_exist:
        c1_ind = names.index("c1")
        c2_ind = names.index("c2")

        bit_0_ind = sum(widths[:c0_ind])
        bit_1_ind = sum(widths[:c1_ind])
        bit_2_ind = sum(widths[:c2_ind])
    else:
        raise ValueError(
            "Could not find a c0 register with 3 bits or c1, c2 and c3 registers with 1 bit each."
        )

    totals = {}

    for result_reversed, count in counts.items():
        # Qiskit reverses the order of the bits in the
        # measurement, so let's undo this
        result = result_reversed[::-1]
        key = result[bit_0_ind] + result[bit_1_ind] + result[bit_2_ind]
        if key in totals:
            totals[key] += count
        else:
            totals[key] = count

    return totals


parser = argparse.ArgumentParser()
parser.add_argument(
    "--eqasm_file",
    "-e",
    type=str,
    default=os.path.join(
        "circuit_files", "qft", "first_order", "qft_order_1_precision_4_ls.eqasm"
    ),
    help="eqasm file with instructions to perform.",
)
files = parser.parse_args()

simulator = QasmSimulator()

qasm_lines = []
with open(files.eqasm_file) as qasm_file:
    for qasm_line in qasm_file:
        if qasm_line.startswith("prep_t"):
            qubit = qasm_line.split()[1][:-1]
            qasm_lines.append(f"h {qubit};\n")
            qasm_lines.append(f"t {qubit};\n")

        elif qasm_line.startswith("prep_y"):
            qubit = qasm_line.split()[1][:-1]
            qasm_lines.append(f"h {qubit};\n")
            qasm_lines.append(f"s {qubit};\n")

        elif qasm_line.startswith("prep_x"):
            qubit = qasm_line.split()[1][:-1]
            qasm_lines.append(f"h {qubit};\n")

        elif qasm_line.startswith("measure_x"):
            qubit, result = tuple(qasm_line[10:-2].split(" -> "))
            qasm_lines.append(f"h {qubit};\n")
            qasm_lines.append(f"measure {qubit} -> {result};\n")

        elif qasm_line.startswith("joint_measure"):
            # Get arguments
            measurements, result = tuple(qasm_line[14:-2].split(" -> "))
            m1, m2 = tuple(measurements.split())
            pauli_1, qubit_1 = tuple(m1.split("*"))
            pauli_2, qubit_2 = tuple(m2.split("*"))

            if (pauli_1 == "z") and (pauli_2 == "z"):
                # Joint ZZ measurement via CNOT
                qasm_lines.append(f"cx {qubit_1},{qubit_2};\n")
                qasm_lines.append(f"measure {qubit_2} -> {result};\n")
                qasm_lines.append(f"cx {qubit_1},{qubit_2};\n")

            elif (pauli_1 == "x") and (pauli_2 == "x"):
                # Joint XX measurement via CNOT and H
                qasm_lines.append(f"h {qubit_1};\n")
                qasm_lines.append(f"h {qubit_2};\n")
                qasm_lines.append(f"cx {qubit_1},{qubit_2};\n")
                qasm_lines.append(f"measure {qubit_2} -> {result};\n")
                qasm_lines.append(f"cx {qubit_1},{qubit_2};\n")
                qasm_lines.append(f"h {qubit_2};\n")
                qasm_lines.append(f"h {qubit_1};\n")

            else:
                raise ValueError(f"Unsupported joint measurement {measurements}")

        else:
            # Standard QASM operation
            qasm_lines.append(qasm_line)

qc = QuantumCircuit.from_qasm_str("".join(qasm_lines))

# Execute the circuit on the qasm simulator
job = simulator.run(qc, shots=10000)

# Grab results from the job
result = job.result()

# Returns counts
counts = result.get_counts(qc)

# Sum over the unwanted classical registers
totals = get_total_counts(qc, counts)

print_counts(totals)
