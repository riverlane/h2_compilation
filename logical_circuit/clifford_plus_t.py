# (c) Copyright Riverlane 2022-2024. All rights reserved.

"""
Circuit for decomposing the H2 QPE circuit into Clifford+T gates,
More generally, one can use any one-qubit Hamiltonian of the for.
H = a1 Z + a2 X.

The decomposition uses circuit identities to transform into
single-qubit phase rotations, then uses gridsynth to synthesise the
decompositions.

There are some optimisations, including taking sequences of S and
T gates and shortening them to at most two gates (equivalent to one
T gate up to correction).
"""

import functools
import subprocess
from math import pi
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, transpile
from qiskit.providers.aer import QasmSimulator
from qiskit.visualization import plot_histogram

from tools import (
    apply_gate_seq,
    get_gridsynth_strings_order_1,
    get_gridsynth_strings_order_2,
    print_counts,
    trotterized_u_order_1,
    trotterized_u_order_2,
)


def get_trotterized_u_fn(
    a1: float, a2: float, second_order: bool = True, bits_precision: int = 5
):
    """
    Return a function that can be used to apply a Trotterized
    version of the time-evolution operator, for a Hamiltonian of
    the form H = a1 Z + a2 X.

    Either a first- or second-order Trotter splitting can be applied.

    Parameters
    ----------
    a1 : float
        Coefficient for the Z operator in the Hamiltonian.
    a2 : float
        Coefficient for the X operator in the Hamiltonian.
    second_order : bool, optional
        If True then apply second-order Trotterization, otherwise
        apply first-order Trotterization.
    bits_precision : int, optional
        The number of bits of precision to use in the
        Clifford + T decomposition.

    Returns
    -------
    trotterized_u : Callable
        A function which takes a qiskit QuantumCircuit and labels for
        control and target qubits on input. It will then modify the
        provided QuantumCircuit by applying the Trotterized U.
    """
    if second_order:
        gate_seq_1, gate_seq_2, gate_seq_1_double = get_gridsynth_strings_order_2(
            a1, a2, bits_precision=bits_precision
        )
        trotterized_u = functools.partial(
            trotterized_u_order_2,
            gate_seq_1=gate_seq_1,
            gate_seq_2=gate_seq_2,
            gate_seq_1_double=gate_seq_1_double,
        )
    else:
        (
            gate_seq_1,
            gate_seq_1_inv,
            gate_seq_2,
            gate_seq_2_inv,
        ) = get_gridsynth_strings_order_1(a1, a2, bits_precision=bits_precision)
        trotterized_u = functools.partial(
            trotterized_u_order_1,
            gate_seq_1=gate_seq_1,
            gate_seq_1_inv=gate_seq_1_inv,
            gate_seq_2=gate_seq_2,
            gate_seq_2_inv=gate_seq_2_inv,
        )

    return trotterized_u


def build_textbook_qpe_circ(trotterized_u: Callable, bits_precision: int = 4):
    """Construct the circuit to perform textbook QPE to 3 bits of
    using the provided Trotterized U operator, performed using a
    single data qubit.

    Parameters
    ----------
    trotterized_u : Callable
        Function which when called will apply a Trotterizd version
        of the controlled unitary to the QuantumCircuit object
        provided, and on the control and target qubits requested.
    bits_precision : int
        The number of bits of precision to use in the
        Clifford + T decomposition.

    Returns
    -------
    qc : qiskit QuantumCircuit
        The constructed QPE circuit.
    """
    # Get the required Gridsynth decompositions, needed for the
    # inverse QFT.
    pi_over_8_seq = subprocess.run(
        ["gridsynth", "-p", f"-b {bits_precision}", str(pi / 8)],
        capture_output=True,
        check=True,
    ).stdout[-2::-1]

    pi_over_8_seq_inv = subprocess.run(
        ["gridsynth", "-p", f"-b {bits_precision}", str(15 * pi / 8)],
        capture_output=True,
        check=True,
    ).stdout[-2::-1]

    q = QuantumRegister(4)
    c = ClassicalRegister(3)

    qc = QuantumCircuit(q, c)

    # Create the HF state
    qc.x(q[3])

    qc.h(q[0])
    qc.h(q[1])
    qc.h(q[2])

    # First bit
    trotterized_u(qc=qc, c=q[2], t=q[3], repetitions=1)

    # Second bit
    trotterized_u(qc=qc, c=q[1], t=q[3], repetitions=2)

    # Third bit
    trotterized_u(qc=qc, c=q[0], t=q[3], repetitions=4)

    # --- Inverse QFT ------
    qc.h(q[0])

    # Decompositon of cphase(-pi/2, q0, q1)
    qc.tdg(q[0])
    qc.tdg(q[1])
    qc.cx(q[0], q[1])
    qc.t(q[1])
    qc.cx(q[0], q[1])

    qc.h(q[1])

    # Decompositon of cphase(-pi/4, q0, q2)
    apply_gate_seq(qc, pi_over_8_seq_inv, q[0])
    apply_gate_seq(qc, pi_over_8_seq_inv, q[2])
    qc.cx(q[0], q[2])
    apply_gate_seq(qc, pi_over_8_seq, q[2])
    qc.cx(q[0], q[2])

    # Decompositon of cphase(-pi/2, q1, q2)
    qc.tdg(q[1])
    qc.tdg(q[2])
    qc.cx(q[1], q[2])
    qc.t(q[2])
    qc.cx(q[1], q[2])

    qc.h(q[2])
    # --- End of Inverse QFT ------

    qc.measure([q[0], q[1], q[2]], c)

    return qc


def build_iqpe_circ(trotterized_u: Callable):
    """Construct the circuit to perform iterative QPE to 3 bits of
    using the provided Trotterized U operator, performed using a
    single data qubit.

    Parameters
    ----------
    trotterized_u : Callable
        Function which when called will apply a Trotterizd version
        of the controlled unitary to the QuantumCircuit object
        provided.

    Returns
    -------
    qc : qiskit QuantumCircuit
        The constructed QPE circuit.
    """
    q = QuantumRegister(2)
    c1 = ClassicalRegister(1)
    c2 = ClassicalRegister(1)
    c3 = ClassicalRegister(1)

    qc = QuantumCircuit(q, c1, c2, c3)

    # --- Create the HF state ------
    qc.x(q[1])

    # --- Iteration 1 ------
    qc.h(q[0])

    trotterized_u(qc=qc, c=q[0], t=q[1], repetitions=4)

    qc.h(q[0])

    qc.measure(q[0], c1)

    # --- Iteration 2 ------
    qc.x(q[0]).c_if(c1, 1)
    qc.h(q[0])

    trotterized_u(qc=qc, c=q[0], t=q[1], repetitions=2)

    # A rotation of -pi/2, which is an inverse S gate, up to a phase
    qc.sdg(q[0]).c_if(c1, 1)

    qc.h(q[0])
    qc.measure(q[0], c2)

    # --- Iteration 3 ------
    qc.x(q[0]).c_if(c2, 1)
    qc.h(q[0])

    trotterized_u(qc=qc, c=q[0], t=q[1], repetitions=1)

    # A rotation of -pi/4, which is an inverse T gate, up to a phase
    qc.tdg(q[0]).c_if(c1, 1)
    # A rotation of -pi/2, which is an inverse S gate, up to a phase
    qc.sdg(q[0]).c_if(c2, 1)

    qc.h(q[0])
    qc.measure(q[0], c3)

    return qc


def run_circ(
    qc,
    simulator,
    nshots,
    qasm_filename,
    bar_filename="bar.png",
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

    # Print the counts
    counts = result.get_counts(transpiled_qc)
    print_counts(counts)

    with open(qasm_filename, "w") as qasm_file:
        qasm_file.write(transpiled_qc.qasm())

    # Plot the frequency graph for each result
    fig = plt.figure()
    plt.bar(counts.keys(), counts.values(), 0.6)
    plt.title("QPE measurement results")
    plt.ylabel("Frequency")
    plt.xlabel("State measured")
    fig.savefig(bar_filename, dpi=fig.dpi)
    plt.show()


if __name__ == "__main__":
    bits_precision = 5
    # Hamiltonian coefficients for H2 on platinum
    # a1 = 0.608374357020626
    # a2 = 0.043033053231386

    # Hamiltonian coefficients for H2 STO-3G at equilibirum
    # geometry (internuclear distance = 0.7414 angstroms)
    a1 = 0.787967358877028
    a2 = 0.181288808211496

    second_order = True
    iqpe = False

    trotterized_u = get_trotterized_u_fn(a1, a2, second_order, bits_precision)

    # Get a QuantumCircuit object for either Textbook QPE or iterative QPE.
    if iqpe:
        qc = build_iqpe_circ(trotterized_u)
    else:
        qc = build_textbook_qpe_circ(trotterized_u, bits_precision=bits_precision)

    simulator = QasmSimulator()
    run_circ(qc, simulator, nshots=10000, qasm_filename="cirq.qasm")
