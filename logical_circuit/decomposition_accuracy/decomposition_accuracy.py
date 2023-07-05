# (c) Copyright Riverlane 2022-2023. All rights reserved.

"""
Assessing decomposition accuracy of gridsynth vs number of gates
produced.

Decomposition uses circuit identities to transform into
single-qubit phase rotations, then uses gridsynth to synthesise the
decompositions.

Slight optimisation by taking sequences of S and T gates and
shortening them to at most two gates (equivalent to one T gate
up to correction).
"""

import numpy as np
from qiskit import transpile
from qiskit.providers.aer import QasmSimulator
from tqdm import tqdm

from logical_circuit.clifford_plus_t import (
    build_iqpe_circ,
    build_textbook_qpe_circ,
    get_trotterized_u_fn,
)


def run_circ(
    qc,
    simulator,
    nshots,
):
    """Given a circuit, run it on the simulator provided and do some
    plotting of the results and the circuit.

    Parameters
    ----------
    qc : qiskit QuantumCircuit
        Circuit to run.
    simulator : qiskit simulator object
        Simulator to perform the circuit on.
    nshots : int
        Number of shots to perform.
    qasm_filename : str
        The name of the QASM file to be created.
    circ_filename : str (optional)
        The name of the circuit image file to be created.
    bar_filename : str (optional)
        The name of the bar plot of the results.
    """
    transpiled_qc = transpile(
        qc,
        basis_gates=["x", "z", "s", "sdg", "t", "tdg", "h", "cx"],
        optimization_level=2,
    )

    # Execute the circuit on the qasm simulator
    job = simulator.run(transpiled_qc, shots=nshots)
    result = job.result()

    # Return the output probabilities
    counts = result.get_counts(transpiled_qc)
    return {key.replace(" ", ""): value / nshots for key, value in counts.items()}


def total_variation_distance(results):
    perfect_results = {
        "000": 0.0095,
        "001": 0.012,
        "010": 0.0133,
        "011": 0.038,
        "100": 0.1229,
        "101": 0.7495,
        "110": 0.0396,
        "111": 0.0152,
    }
    return sum(abs(results[key] - perfect_results[key]) for key in results.keys())


if __name__ == "__main__":
    with open("decomposition_accuracy.csv", "w") as output_file:
        print(
            "bits_precision",
            "mean_textbook_circuit_lengths",
            "std_textbook_circuit_lengths",
            "mean_textbook_circuit_distance",
            "std_textbook_circuit_distance",
            "mean_iterative_circuit_lengths",
            "std_iterative_circuit_lengths",
            "mean_iterative_circuit_distance",
            "std_iterative_circuit_distance",
            sep=",",
            file=output_file,
        )
        for bits_precision in range(1, 33):
            a1 = 0.787967358877028
            a2 = 0.181288808211496

            textbook_circuit_lengths = []
            textbook_circuit_results = []
            iterative_circuit_lengths = []
            iterative_circuit_results = []
            print(bits_precision)
            for _ in tqdm(range(1000)):
                trotterized_u = get_trotterized_u_fn(a1, a2, bits_precision)

                textbook_qc = build_textbook_qpe_circ(
                    trotterized_u, bits_precision=bits_precision
                )
                iterative_qc = build_iqpe_circ(trotterized_u)

                simulator = QasmSimulator()
                textbook_circuit_lengths.append(len(textbook_qc.data))
                textbook_circuit_results.append(
                    total_variation_distance(
                        run_circ(textbook_qc, simulator, nshots=10000)
                    )
                )
                iterative_circuit_lengths.append(len(iterative_qc.data))
                iterative_circuit_results.append(
                    total_variation_distance(
                        run_circ(iterative_qc, simulator, nshots=10000)
                    )
                )

            print(
                bits_precision,
                np.mean(textbook_circuit_lengths),
                np.std(textbook_circuit_lengths),
                np.mean(textbook_circuit_results),
                np.std(textbook_circuit_results),
                np.mean(iterative_circuit_lengths),
                np.std(iterative_circuit_lengths),
                np.mean(iterative_circuit_results),
                np.std(iterative_circuit_results),
                sep=",",
                file=output_file,
            )
