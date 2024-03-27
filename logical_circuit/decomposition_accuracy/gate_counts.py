# (c) Copyright Riverlane 2022-2024. All rights reserved.

"""
Circuit for decomposing the H2 QPE circuit into Clifford+T.

Decomposition uses circuit identities to transform into
single-qubit phase rotations, then uses gridsynth to synthesise the
decompositions.

Slight optimisation by taking sequences of S and T gates and
shortening them to at most two gates (equivalent to one T gate
up to correction).
"""

from collections import Counter

from tqdm import tqdm

from logical_circuit.clifford_plus_t import (
    build_iqpe_circ,
    build_textbook_qpe_circ,
    get_trotterized_u_fn,
)

if __name__ == "__main__":
    bits_precision = 10
    # Hamiltonian coefficients for H2 STO-3G at equilibrium
    # geometry (internuclear distance = 0.7414 angstroms)
    a1 = 0.787967358877028
    a2 = 0.181288808211496

    second_order = True

    gate_counts = dict()

    for _ in tqdm(range(1000)):
        trotterized_u = get_trotterized_u_fn(a1, a2, second_order, bits_precision)

        qc = build_iqpe_circ(trotterized_u)

        phase_gates = set()
        gates = Counter()
        for gate in qc.data:
            gate_type = gate.operation.name
            if gate_type in ["z", "s", "sdg", "t", "tdg"]:
                phase_gates.add(gate_type)
            else:
                if phase_gates:
                    if {"t", "tdg"} & phase_gates:
                        gates["t_like"] += 1
                    elif {"s", "sdg"} & phase_gates:
                        gates["s_like"] += 1
                    elif "z" in phase_gates:
                        gates["z"] += 1
                    phase_gates = set()
                gates[gate_type] += 1
        for gate_type, gate_count in gates.items():
            gate_counts[gate_type] = gate_counts.get(gate_type, []) + [gate_count]

    print(gate_counts)
