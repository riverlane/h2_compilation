# (c) Copyright Riverlane 2022-2023. All rights reserved.

import math
import os
import sys
from collections import Counter

import pandas
from qiskit import QuantumCircuit
from scipy.optimize import brentq

ERROR_BUDGET = 1e-2
D_UPPER_BOUND = 1e4

# Number of QEC rounds per gate type in do Cliffords model.
# Represented as tuples (a, b)
# such that a gate requires a*d+b QEC rounds.
gate_cost_do_cliffords = {
    "h": (3, 4),
    "t_like": (2.5, 4),
    "cx": (3, 4),
    "s_like": (1.5, 3),
    "measure": (0, 1),
}

# Number of QEC rounds per gate type in Litinski model.
# Represented as tuples (a, b)
# such that a gate requires a*d+b QEC rounds.
gate_cost_commute_cliffords = {"t_like": (1, 1), "measure": (1, 0)}


def num_rounds(gates, gate_cost, d):
    """Number of QEC rounds required to implement a given list of gates
    at a given distance.
    """
    return sum(
        gate_count * (gate_cost[gate][0] * d + gate_cost[gate][1])
        for gate, gate_count in gates.items()
        if gate in gate_cost
    )


def overall_logical_error(gates, gate_cost, num_logical_qubits, physical_error_rate, d):
    """Probability of a logical failure not including magic state distillation."""
    return (
        num_logical_qubits
        * num_rounds(gates, gate_cost, d)
        * 0.1
        * (100 * physical_error_rate) ** ((d + 1) / 2)
    )


circuit = QuantumCircuit.from_qasm_file(sys.argv[1])

# First get the number of each type of gate.
phase_gates = set()
gates = Counter()
for gate in circuit.data:
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

if __name__ == "__main__":
    factory_resources = pandas.read_csv(
        os.path.join("resource_estimates", "factory_resources.csv")
    )

    for physical_error_rate in [1e-3, 1e-4]:
        print("physical error rate:", physical_error_rate)

        # Load factory information.
        factory = factory_resources.loc[
            factory_resources["physical_error_rate"] == physical_error_rate
        ]
        print("    Factory type: ", factory["type"])
        print("    Factory X distance: ", factory["d_x"])
        print("    Factory Z distance: ", factory["d_z"])
        print("    Factory measurement distance: ", factory["d_m"])
        distillation_time = float(factory["distillation_time"])
        distillation_qubits = int(factory["distillation_qubits"])
        distillation_error = float(factory["distillation_error"])
        print("    Distillation time:", distillation_time)
        print("    Number of qubits for single factory:", distillation_qubits)
        print("    Distillation error probability:", distillation_error)
        print(
            "    Distillation failure probability:",
            factory["distillation_failure_prob"],
        )

        def error_rate_given_distance_do_cliffords(distance):
            return (
                overall_logical_error(
                    gates=gates,
                    gate_cost=gate_cost_do_cliffords,
                    num_logical_qubits=4,
                    physical_error_rate=physical_error_rate,
                    d=distance,
                )
                - ERROR_BUDGET
            )

        def error_rate_given_distance_commute_cliffords(distance):
            return (
                overall_logical_error(
                    gates=gates,
                    gate_cost=gate_cost_commute_cliffords,
                    num_logical_qubits=6,
                    physical_error_rate=physical_error_rate,
                    d=distance,
                )
                - ERROR_BUDGET
            )

        # Do Cliffords resource estimates.
        # Find distance to get error rate within budget.
        distance_do_cliffords = math.ceil(
            brentq(error_rate_given_distance_do_cliffords, a=1, b=D_UPPER_BOUND)
        )

        # Estimate circuit properties (number of qubits, number of rounds
        # number of rounds per T state, and data error)
        num_physical_qubits_do_cliffords = 2 * (2 * distance_do_cliffords + 2) ** 2
        num_rounds_per_t_state_do_cliffords = 4 * distance_do_cliffords + 5
        num_rounds_do_cliffords = num_rounds(
            gates, gate_cost_do_cliffords, distance_do_cliffords
        )
        data_error_do_cliffords = overall_logical_error(
            gates=gates,
            gate_cost=gate_cost_do_cliffords,
            num_logical_qubits=4,
            physical_error_rate=physical_error_rate,
            d=distance_do_cliffords,
        )

        # T gate error budget estimated by remaining error budget divided by
        # number of T gates.
        t_error_do_cliffords = (ERROR_BUDGET - data_error_do_cliffords) / gates[
            "t_like"
        ]
        print("    Do Cliffords model")
        for num_factories in range(1, 5):
            # Find number of factories required to generate T states at desired rate.
            if distillation_time / num_factories <= num_rounds_per_t_state_do_cliffords:
                print("        num factories:", num_factories)
                print(
                    "        Previous error without storage:", data_error_do_cliffords
                )

                # Update data error given extra patches for storing T states.
                data_error_do_cliffords = overall_logical_error(
                    gates=gates,
                    gate_cost=gate_cost_do_cliffords,
                    num_logical_qubits=4 + num_factories,
                    physical_error_rate=physical_error_rate,
                    d=distance_do_cliffords,
                )

                print("        Previous error with storage:", data_error_do_cliffords)
                # If no longer in error budget, increase distance and related parameters
                while (
                    data_error_do_cliffords + distillation_error * gates["t_like"]
                    > ERROR_BUDGET
                ):
                    distance_do_cliffords += 1
                    data_error_do_cliffords = overall_logical_error(
                        gates=gates,
                        gate_cost=gate_cost_do_cliffords,
                        num_logical_qubits=4 + num_factories,
                        physical_error_rate=physical_error_rate,
                        d=distance_do_cliffords,
                    )
                num_physical_qubits_do_cliffords = (
                    2 * (2 * distance_do_cliffords + 2) ** 2
                )
                num_rounds_per_t_state_do_cliffords = 4 * distance_do_cliffords + 5
                num_rounds_do_cliffords = num_rounds(
                    gates, gate_cost_do_cliffords, distance_do_cliffords
                )
                print(
                    "        Physical qubits for storage:",
                    2 * num_factories * (distance_do_cliffords**2),
                )
                total_physical_qubits_do_cliffords = (
                    num_physical_qubits_do_cliffords
                    + num_factories
                    * (distillation_qubits + 2 * (distance_do_cliffords**2))
                )
                break
        else:
            # Even with four factories T states are not produced fast enough
            print("        num factories: 4")
            print("        time limited by distillation")
            num_rounds_do_cliffords = distillation_time * gates["t_like"] / 4
            total_physical_qubits_do_cliffords = (
                num_physical_qubits_do_cliffords + 4 * distillation_qubits
            )
        print("        distance:", distance_do_cliffords)
        print("        data error:", data_error_do_cliffords)
        print(
            "        num physical qubits for logical patches:",
            num_physical_qubits_do_cliffords,
        )
        print("        num rounds per t state:", num_rounds_per_t_state_do_cliffords)
        print("        T state error budget:", t_error_do_cliffords)
        print("        num rounds:", num_rounds_do_cliffords)
        print("        total physical qubits:", total_physical_qubits_do_cliffords)
        print(
            "        total error:",
            data_error_do_cliffords + distillation_error * gates["t_like"],
        )

        # Litinski resource estimates.
        # Find distance to get error rate within budget.
        distance_commute_cliffords = math.ceil(
            brentq(error_rate_given_distance_commute_cliffords, a=1, b=D_UPPER_BOUND)
        )

        # Estimate circuit properties (number of qubits, number of rounds
        # number of rounds per T state, and data error)
        num_physical_qubits_commute_cliffords = (
            2
            * (3 * distance_commute_cliffords + 4)
            * (2 * distance_commute_cliffords + 2)
        )
        num_rounds_per_t_state_commute_cliffords = distance_commute_cliffords + 1
        num_rounds_commute_cliffords = num_rounds(
            gates, gate_cost_commute_cliffords, distance_commute_cliffords
        )
        data_error_commute_cliffords = overall_logical_error(
            gates=gates,
            gate_cost=gate_cost_commute_cliffords,
            num_logical_qubits=6,
            physical_error_rate=physical_error_rate,
            d=distance_commute_cliffords,
        )

        # T gate error budget estimated by remaining error budget divided by
        # number of T gates.
        t_error_commute_cliffords = (
            ERROR_BUDGET - data_error_commute_cliffords
        ) / gates["t_like"]
        print("    Commute Cliffords model")
        for num_factories in range(1, 5):
            # Find number of factories required to generate T states at desired rate.
            if (
                distillation_time / num_factories
                <= num_rounds_per_t_state_commute_cliffords
            ):
                print("        num factories:", num_factories)
                print(
                    "        Previous error without storage:",
                    data_error_commute_cliffords,
                )

                # Update data error given extra patches for storing T states.
                data_error_commute_cliffords = overall_logical_error(
                    gates=gates,
                    gate_cost=gate_cost_commute_cliffords,
                    num_logical_qubits=6 + num_factories,
                    physical_error_rate=physical_error_rate,
                    d=distance_commute_cliffords,
                )
                print(
                    "        Previous error with storage:",
                    data_error_commute_cliffords,
                    data_error_commute_cliffords + distillation_error,
                )
                # If no longer in error budget, increase distance and related parameters
                while (
                    data_error_commute_cliffords + distillation_error * gates["t_like"]
                    > ERROR_BUDGET
                ):
                    distance_commute_cliffords += 1
                    data_error_commute_cliffords = overall_logical_error(
                        gates=gates,
                        gate_cost=gate_cost_commute_cliffords,
                        num_logical_qubits=6 + num_factories,
                        physical_error_rate=physical_error_rate,
                        d=distance_commute_cliffords,
                    )
                num_physical_qubits_commute_cliffords = (
                    2
                    * (3 * distance_commute_cliffords + 4)
                    * (2 * distance_commute_cliffords + 2)
                )
                num_rounds_per_t_state_commute_cliffords = (
                    distance_commute_cliffords + 1
                )
                num_rounds_commute_cliffords = num_rounds(
                    gates, gate_cost_commute_cliffords, distance_commute_cliffords
                )
                print(
                    "        Physical qubits for storage:",
                    2 * num_factories * (distance_commute_cliffords**2),
                )
                total_physical_qubits_commute_cliffords = (
                    num_physical_qubits_commute_cliffords
                    + num_factories
                    * (distillation_qubits + 2 * (distance_commute_cliffords**2))
                )
                break
        else:
            # Even with four factories T states are not produced fast enough
            print("        num factories: 4")
            print("        time limited by distillation")
            num_rounds_commute_cliffords = distillation_time * gates["t_like"] / 4
            total_physical_qubits_commute_cliffords = (
                num_physical_qubits_commute_cliffords + 4 * distillation_qubits
            )
        print("        distance:", distance_commute_cliffords)
        print("        data error:", data_error_commute_cliffords)
        print("        num rounds:", num_rounds_commute_cliffords)
        print("        num physical qubits:", num_physical_qubits_commute_cliffords)
        print(
            "        num rounds per t state:", num_rounds_per_t_state_commute_cliffords
        )
        print("        T state error budget:", t_error_commute_cliffords)
        print("        num rounds:", num_rounds_commute_cliffords)
        print("        total physical qubits:", total_physical_qubits_commute_cliffords)
        print(
            "        total error:",
            data_error_commute_cliffords + distillation_error * gates["t_like"],
        )
