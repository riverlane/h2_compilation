# (c) Copyright Riverlane 2022-2023. All rights reserved.

# Count the number of times a Pauli product is applied.

import sys
from collections import Counter

from commute_paulis import parse_conditions

if __name__ == "__main__":
    paulis = []
    with open(sys.argv[1]) as paulis_file:
        # Parse instructions file.
        for instruction in paulis_file:
            terms = instruction[:-1].split(",")
            paulis.append(tuple(terms[2:-2]))

    # Get unique condition branches.
    counts = Counter(paulis)
    for product, count in counts.most_common():
        print(product, count)
