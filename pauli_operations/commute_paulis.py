# (c) Copyright Riverlane 2022-2023. All rights reserved.

# Takes a file of Pauli product rotations and
# commutes the Clifford operations to after the measurements.

import re
import sys
from typing import Dict, List, Tuple

from to_pauli_ops import write_condition

# This dictionary maps two Paulis to a tuple specifying
# whether or not they commute and the modified Pauli.
#
# Specifically, the first element of the value is whether
# or not the Paulis commute in the first place.
#
# The second and third elements are the phase and
# what the second Pauli becomes after the first
# Pauli is commuted through.
#
# For example, if we look at X and Z we have:
# XZ = -YX
#
# So ("x", "z") do not commute,
# their commutation provides a -1 phase,
# and the Z Pauli becomes a Y Pauli after commutation.
COMMUTING_RULES = {
    ("i", "i"): (True, 1, "i"),
    ("i", "x"): (True, 1, "x"),
    ("i", "y"): (True, 1, "y"),
    ("i", "z"): (True, 1, "z"),
    ("x", "i"): (True, 1, "x"),
    ("x", "x"): (True, 1, "x"),
    ("x", "y"): (False, -1, "z"),
    ("x", "z"): (False, 1, "y"),
    ("y", "i"): (True, 1, "y"),
    ("y", "x"): (False, 1, "z"),
    ("y", "y"): (True, 1, "y"),
    ("y", "z"): (False, -1, "x"),
    ("z", "i"): (True, 1, "z"),
    ("z", "x"): (False, -1, "y"),
    ("z", "y"): (False, 1, "x"),
    ("z", "z"): (True, 1, "z"),
}


def parse_conditions(conditions: str) -> Dict[str, str]:
    """Splits a condition string up into pairs of
    bit indexes and their condition value.

    Parameters
    ----------
    conditions : str
        The string format used for saving conditions.
        Written as a series of clauses eg
        (0==0)&&(1==0)&&(2==1)

        This example corresponds to:
        - bit 0 must be 0
        - bit 1 must be 0
        - bit 2 must be 1

    Returns
    -------
    Dict[str, str]
        A dictionary mapping the bit indexes to the values.

        For the example above the dictionary becomes:
        {0:0, 1:0, 2:1}
    """
    if conditions:
        return {
            clause.split("==")[0][1:]: clause.split("==")[1][:-1]
            for clause in conditions.split("&&")
        }
    else:
        return {}


def parse_paulis_file(file_path):
    """Parse the Pauli product rotations CSV file.

    Parameters
    ----------
    file_path
        File path for the Pauli CSV file.

    Returns
    -------
    List
        List of the Pauli product rotations.
        Each Pauli product rotation consists of:
        - an instruction (either "rotate" or "measure")
        - the angle if the instruction is "rotate"
        - the bases used in the Pauli product
        - the classical bit the result is saved to
          if the instruction is "measure"
        - Any conditions under which the operation is applied
    """
    rotations = []
    with open(file_path) as paulis_file:
        for line in paulis_file:
            terms = line[:-1].split(",")
            instruction = terms[0]
            if re.match("-?\d+", terms[1]) is not None:
                angle = int(terms[1])
            else:
                angle = 1
            bases = terms[2:-2]
            cbit = terms[-2]
            conditions = parse_conditions(terms[-1])
            rotations.append((instruction, angle, bases, cbit, conditions))
    return rotations


def commuted_pauli_rotations(
    angle: int,
    first_paulis: List[str],
    second_paulis: List[str],
    first_conditions: Dict[str, str],
    second_conditions: Dict[str, str],
) -> List[Tuple[int, List[str], Dict[str, str]]]:
    """Given two Pauli product rotations, work out the commutation update rules.
    This is based on the commutation rules in Figure 4 of
    https://quantum-journal.org/papers/q-2019-03-05-128/

    Parameters
    ----------
    angle : int
        Angle of rotation for the second Pauli,
        specified as an integer n where the angle is pi/n.
        Note it is assumed the first angle is always pi/4.
    first_paulis : List[str]
        Paulis used in first operation, which will stay
        the same after commutation.
    second_paulis : List[str]
        Paulis used in second operation, which may change
        after commutation.
    first_conditions : Dict[str, str]
        Conditions on which the first operation runs.
        Note there should only be one condition specified.
    second_conditions : Dict[str, str]
        Conditions on which the second operation runs.

    Returns
    -------
    List[Tuple[int, List[str], Dict[str, str]]]
        List of the second Pauli Product Rotations after commutation.
        Note that only the second Pauli Product Rotation is changed,
        as the commutation rules leave the first Pauli Product Rotation
        invariant.
        Note there might be new rotations if the first
        operation has extra conditions, as this will affect
        the exact operation we apply after commutation.
        The integer suggests phase to change the angle,
        either +/-1.
        The list of strings is a list of the new Pauli operations.
        The Dictionary is new conditions to add.
    """
    commute = True
    commuted_paulis = []
    phase = 1 if angle > 0 else -1
    for bit, value in first_conditions.items():
        if bit in second_conditions and second_conditions[bit] != value:
            # Contradicting conditions, so operations commute
            return [(1, second_paulis, {})]
    for first_pauli, second_pauli in zip(first_paulis, second_paulis):
        commutation_rule = COMMUTING_RULES[(first_pauli, second_pauli)]
        commute ^= not commutation_rule[0]
        phase *= commutation_rule[1]
        commuted_paulis.append(commutation_rule[2])
    if commute:
        # Paulis commute, so nothing changes
        return [(1, second_paulis, {})]
    elif abs(angle) == 2:
        if first_conditions and not (
            first_conditions.items() <= second_conditions.items()
        ):
            # Paulis don't commute, add separate rotations
            # for conditions from clifford rotation
            return [
                (-1, second_paulis, first_conditions),
                (
                    1,
                    second_paulis,
                    {
                        bit: str((int(value) + 1) % 2)
                        for bit, value in first_conditions.items()
                    },
                ),
            ]
        else:
            # Paulis don't commute but no new conditions
            return [(-1, second_paulis, {})]
    else:
        if first_conditions and not (
            first_conditions.items() <= second_conditions.items()
        ):
            # Paulis don't commute, add separate rotations
            # for conditions from clifford rotation
            return [
                (phase, commuted_paulis, first_conditions),
                (
                    1,
                    second_paulis,
                    {
                        bit: str((int(value) + 1) % 2)
                        for bit, value in first_conditions.items()
                    },
                ),
            ]
        else:
            # Paulis don't commute but no new conditions
            return [(phase, commuted_paulis, {})]


def commute_cliffords_to_end(rotations):
    """Commute the pi/4 rotations to the end of the circuit.

    Parameters
    ----------
    rotations
        List of Pauli product rotations including pi/4 rotations.

    Returns
    -------
    List
        Modified list consisting only of pi/8 rotations
        and measurements.
    """
    for clifford_index in range(len(rotations) - 1, -1, -1):
        instruction, angle, bases, cbit, conditions = rotations[clifford_index]
        if instruction == "rotate" and 2 <= abs(angle) <= 4:
            # Clifford operation, so we commute it to the end of the circuit.
            del rotations[clifford_index]
            t_index = clifford_index
            while t_index < len(rotations):
                t_instruction, t_angle, t_bases, t_cbit, t_conditions = rotations[
                    t_index
                ]
                del rotations[t_index]
                commuted_updates = commuted_pauli_rotations(
                    angle, bases, t_bases, conditions, t_conditions
                )
                for phase, commuted_bases, condition_updates in commuted_updates:
                    # Add new commuted pi/8 rotations and measurements.
                    new_angle = t_angle * phase
                    rotations.insert(
                        t_index,
                        (
                            t_instruction,
                            new_angle,
                            commuted_bases,
                            t_cbit,
                            {**t_conditions, **condition_updates},
                        ),
                    )
                t_index += len(commuted_updates)
    return rotations


if __name__ == "__main__":
    rotations = parse_paulis_file(sys.argv[1])

    commuted_rotations = commute_cliffords_to_end(rotations)

    output_name = f"{'.'.join(sys.argv[1].split('.')[:-1])}_commuted.csv"

    with open(output_name, "w") as output_file:
        # Save remaining rotations and measurements to file.
        for instruction, angle, bases, cbit, conditions in commuted_rotations:
            output_file.write(
                f"{instruction},{angle},{','.join(bases)},{cbit},{write_condition(conditions)}\n"
            )
