# (c) Copyright Riverlane 2022-2024. All rights reserved.

import subprocess
from collections import Counter
from math import pi


def get_gridsynth_strings_order_1(a1: float, a2: float, bits_precision: int = 4):
    """
    Run gridsynth to perform a Clifford+T decomposition of the
    RZ gates needed to perform the time-evolution U operator,
    for a Hamiltonian of the form H = a1 Z + a2 X.

    This considers the required operators for first-order
    Trotterization with a single Trotter step.

    Parameters
    ----------
    a1 : float
        Coefficient for the Z operator in the Hamiltonian.
    a2 : float
        Coefficient for the X operator in the Hamiltonian.
    bits_precision : int, optional
        The number of bits of precision to use in the
        Clifford + T decomposition.

    Returns
    -------
    gate_seq_1 : bytes
        The gridsynth decomposition of the RZ(-a1*t).
    gate_seq_1_inv : bytes
        The gridsynth decomposition of the RZ(a1*t).
    gate_seq_2 : bytes
        The gridsynth decomposition of the RZ(-a2*t).
    gate_seq_2_inv : bytes
        The gridsynth decomposition of the RZ(a2*t).
    """
    # Time step so that eigenvalues of U are between -0.5 and +0.5
    t = 2 * pi / (2 * (a1 + a2))

    # We want to perform e^{i*a1*t Z/2} and e^{i*a2*t Z/2} and
    # their inverses. Note that we divide by 2 because of the
    # decomposition of controlled-RZ into CNOT+RZ - in this
    # decomposition the angles are halved relative to those in
    # the controlled-RZ.

    # Work out angles for gridsynth.
    # We multiply by -2 because an RZ gate is defined as
    # RZ(theta) = e^{-i (theta/2) Z}.
    angle_1 = (-2.0 * t * a1) / 2
    angle_1_inv = -angle_1
    while angle_1 <= 0:
        angle_1 += 2 * pi
    while angle_1_inv <= 0:
        angle_1_inv += 2 * pi

    angle_2 = (-2.0 * t * a2) / 2
    angle_2_inv = -angle_2
    while angle_2 <= 0:
        angle_2 += 2 * pi
    while angle_2_inv <= 0:
        angle_2_inv += 2 * pi

    gate_seq_1 = subprocess.run(
        ["gridsynth", "-p", f"-b {bits_precision}", str(angle_1)],
        capture_output=True,
        check=True,
    ).stdout[-2::-1]

    gate_seq_1_inv = subprocess.run(
        ["gridsynth", "-p", f"-b {bits_precision}", str(angle_1_inv)],
        capture_output=True,
        check=True,
    ).stdout[-2::-1]

    gate_seq_2 = subprocess.run(
        ["gridsynth", "-p", f"-b {bits_precision}", str(angle_2)],
        capture_output=True,
        check=True,
    ).stdout[-2::-1]

    gate_seq_2_inv = subprocess.run(
        ["gridsynth", "-p", f"-b {bits_precision}", str(angle_2_inv)],
        capture_output=True,
        check=True,
    ).stdout[-2::-1]

    return gate_seq_1, gate_seq_1_inv, gate_seq_2, gate_seq_2_inv


def get_gridsynth_strings_order_2(a1: float, a2: float, bits_precision: int = 4):
    """
    Run gridsynth to perform a Clifford+T decomposition of the
    RZ gates needed to perform the time-evolution U operator,
    for a Hamiltonian of the form H = a1 Z + a2 X.

    This considers the required operators for second-order
    Trotterization with a single Trotter step.

    Parameters
    ----------
    a1 : float
        Coefficient for the Z operator in the Hamiltonian.
    a2 : float
        Coefficient for the X operator in the Hamiltonian.
    bits_precision : int, optional
        The number of bits of precision to use in the
        Clifford + T decomposition.

    Returns
    -------
    gate_seq_1 : bytes
        The gridsynth decomposition of the RZ(a1*t/2).
    gate_seq_2 : bytes
        The gridsynth decomposition of the RZ(a2*t).
    gate_seq_1_double : bytes
        The gridsynth decomposition of the RZ(a1*t).
    """
    # Time step so that eigenvalues of U are between -0.5 and +0.5
    t = 2 * pi / (2 * (a1 + a2))

    # We want to perform e^{-i*(a1*t/4) Z} and e^{-i*(a2*t/2) Z}.
    # These are equal to RZ(a1*t/2) and RZ(a2*t).

    # Work out angles for gridsynth. Note that we multiply by 2
    # because an RZ gate is defined as RZ(theta) = e^{-i (theta/2) Z}.
    angle_1 = (2.0 * t * a1) / 4
    while angle_1 <= 0:
        angle_1 += 2 * pi

    angle_2 = (2.0 * t * a2) / 2
    while angle_2 <= 0:
        angle_2 += 2 * pi

    gate_seq_1 = subprocess.run(
        ["gridsynth", "-p", f"-b {bits_precision}", str(angle_1)],
        capture_output=True,
        check=True,
    ).stdout[-2::-1]

    gate_seq_2 = subprocess.run(
        ["gridsynth", "-p", f"-b {bits_precision}", str(angle_2)],
        capture_output=True,
        check=True,
    ).stdout[-2::-1]

    gate_seq_1_double = subprocess.run(
        ["gridsynth", "-p", f"-b {bits_precision}", str(angle_1 * 2)],
        capture_output=True,
        check=True,
    ).stdout[-2::-1]

    return gate_seq_1, gate_seq_2, gate_seq_1_double


def print_counts(counts):
    """Print the measurement counts from an experiment in a
    slightly more neat way than just doing print(counts). This
    also defines an order for the printing, which is useful
    for comparisons.

    This currently assumes that 3 bits were measured, either into
    a single ClassicalRegister of size 3, or 3 ClassicalRegister
    objects of size 1.

    Parameters
    ----------
    counts : dict or Counter
        Dictionary containing the number of measurements for each
        result. The keys are strings, the values are integers.
    """
    order_1 = ["000", "001", "010", "011", "100", "101", "110", "111"]
    order_2 = [
        "0 0 0",
        "0 0 1",
        "0 1 0",
        "0 1 1",
        "1 0 0",
        "1 0 1",
        "1 1 0",
        "1 1 1",
    ]
    # For textbook QPE we measure into a single classical register
    # of size 3. For iQPE we measure into three classical registers
    # of size 1. The results will be labelled either as in order_1
    # or order_2 depending on this. Here we find which it was.
    if any(i in counts for i in order_1):
        order = order_1
    elif any(i in counts for i in order_2):
        order = order_2
    else:
        raise ValueError("The counts object provided is not supported by print_counts.")

    print("Final measurement counts:")
    for i in order:
        if i in counts:
            print(i, ":", counts[i])
        else:
            print(i, ":", "0")


def apply_t_gates(qc, t_count, qubit):
    """Apply operation to the QuantumCircuit (qc) object provided,
    equivalent to the number of T gates required

    Parameters
    ----------
    qc : qiskit QuantumCircuit
        qiskit circuit.
    t_count : int
        Number of T (and S=T*2) gates.
    qubit : int or qiskit.circuit.quantumregister.Qubit
        Index to apply gate to.
    """
    t_count = t_count & 7  # modulo 8
    if t_count == 1:
        # One T gate
        qc.t(qubit)
    elif t_count == 2:
        # One S gate
        qc.s(qubit)
    elif t_count == 3:
        # One Z gate and one T^-1 gate
        # Equivalent to one T gate and correction
        qc.z(qubit)
        qc.tdg(qubit)
    elif t_count == 4:
        # One Z gate
        qc.z(qubit)
    elif t_count == 5:
        # One Z gate and one T gate
        # Equivalent to one T gate and correction
        qc.z(qubit)
        qc.t(qubit)
    elif t_count == 6:
        # One S^-1 gate
        qc.sdg(qubit)
    elif t_count == 7:
        # One T^-1 gate
        qc.tdg(qubit)


def apply_gate_seq(qc, gate_seq, qubit):
    """Apply gridsynth sequence of gates to the qubit requested
    in the QuantumCircuit object (qc) provided.

    Parameters
    ----------
    qc : qiskit QuantumCircuit
        qiskit circuit.
    gate_seq : bytes
        Sequence of gates as byte string.
    qubit : int or qiskit.circuit.quantumregister.Qubit
        Index of qubit to apply gates to.

    Raises
    ------
    ValueError
        Gate is not recognised.
    """
    t_count = 0
    for gate in gate_seq:
        gate = chr(gate)
        if gate == "T":
            t_count = t_count + 1
        elif gate == "S":
            t_count = t_count + 2
        elif gate == "I":
            continue
        else:
            apply_t_gates(qc, t_count, qubit)
            t_count = 0
            if gate == "H":
                qc.h(qubit)
            elif gate == "X":
                qc.x(qubit)
            else:
                raise ValueError(f"Unrecognised gate {gate}")
    apply_t_gates(qc, t_count, qubit)


def trotterized_u_order_1(
    qc, c, t, gate_seq_1, gate_seq_1_inv, gate_seq_2, gate_seq_2_inv, repetitions
):
    """Apply the Trotterized version of the time evolution operator
    U using first-order Trotterization, to the QuantumCircuit object
    (qc) provided.

    Parameters
    ----------
    qc : qiskit QuantumCircuit
        Circuit to apply the unitary to.
    c : int or qiskit.circuit.quantumregister.Qubit
        Label of the control qubit.
    t : int or qiskit.circuit.quantumregister.Qubit
        Label of the target qubit.
    gate_seq_1 : bytes
        The gridsynth decomposition of the RZ(-a_1*t).
    gate_seq_1_inv : bytes
        The gridsynth decomposition of the RZ(a_1*t).
    gate_seq_2 : bytes
        The gridsynth decomposition of the RZ(-a_2*t).
    gate_seq_2_inv : bytes
        The gridsynth decomposition of the RZ(a_2*t).
    repetitions : int
        Number of times to repeat the Trotter step.
    """
    # Note that the control qubit in the CNOT is the target qubit
    # entered by the user. This is not a mistake! This is just how
    # the decomposition of controlled-RZ into CNOT+RZ happens to work.

    for _ in range(repetitions):
        # First apply the controlled-RZ:
        qc.cx(t, c)
        apply_gate_seq(qc, gate_seq_1_inv, c)
        apply_gate_seq(qc, gate_seq_1, t)
        qc.cx(t, c)
        # Then apply the controlled-RX:
        qc.h(t)
        qc.cx(t, c)
        apply_gate_seq(qc, gate_seq_2_inv, c)
        apply_gate_seq(qc, gate_seq_2, t)
        qc.cx(t, c)
        qc.h(t)


def trotterized_u_order_2(
    qc, c, t, gate_seq_1, gate_seq_2, gate_seq_1_double, repetitions
):
    """Apply the Trotterized version of the time evolution operator
    U using second-order Trotterization, to the QuantumCircuit object
    (qc) provided.

    Parameters
    ----------
    qc : qiskit QuantumCircuit
        Circuit to apply the unitary to.
    c : int or qiskit.circuit.quantumregister.Qubit
        Label of the control qubit.
    t : int or qiskit.circuit.quantumregister.Qubit
        Label of the target qubit.
    gate_seq_1 : bytes
        The gridsynth decomposition of the RZ(a_1*t/2).
    gate_seq_2 : bytes
        The gridsynth decomposition of the RZ(a_2*t).
    gate_seq_1_double : bytes
        The gridsynth decomposition of the RZ(a_1*t).
    repetitions : int
        Number of times to repeat the Trotter step.
    """
    # First apply the controlled-RZ:
    qc.cx(c, t)
    apply_gate_seq(qc, gate_seq_1, t)
    qc.cx(c, t)
    # Then apply the controlled-RX:
    qc.h(t)
    qc.cx(c, t)
    apply_gate_seq(qc, gate_seq_2, t)
    qc.cx(c, t)
    qc.h(t)
    for _ in range(repetitions - 1):
        qc.cx(c, t)
        apply_gate_seq(qc, gate_seq_1_double, t)
        qc.cx(c, t)
        # Then apply the controlled-RX:
        qc.h(t)
        qc.cx(c, t)
        apply_gate_seq(qc, gate_seq_2, t)
        qc.cx(c, t)
        qc.h(t)
    # And the final controlled-RZ:
    qc.cx(c, t)
    apply_gate_seq(qc, gate_seq_1, t)
    qc.cx(c, t)
