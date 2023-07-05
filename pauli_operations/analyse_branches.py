# (c) Copyright Riverlane 2022-2023. All rights reserved.

"""
For each condition count the number of operations (measurements and rotations)
that are applied when that condition holds.
"""

import sys
from collections import Counter

from commute_paulis import parse_conditions

if __name__ == "__main__":
    rotations = []
    with open(sys.argv[1]) as paulis_file:
        # Parse instructions file.
        for instruction in paulis_file:
            terms = instruction[:-1].split(",")
            rotations.append((terms[0], parse_conditions(terms[-1])))

    # Get unique condition branches.
    conditions = set(tuple(sorted(condition.items())) for _, condition in rotations)
    for condition in conditions:
        # Count the number of instructions which appear in that branch.
        counts = Counter(
            instruction
            for instruction, cond in rotations
            if set(cond.items()) <= set(condition)
        )
        print(condition, counts)
