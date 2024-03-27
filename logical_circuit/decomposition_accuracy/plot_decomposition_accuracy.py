# (c) Copyright Riverlane 2022-2024. All rights reserved.

import math
import sys

import matplotlib.pyplot as plt
import pandas as pd

data = pd.read_csv(sys.argv[1])

accuracy_fig = plt.figure()

plt.errorbar(
    data["bits_precision"],
    [mean / 2 for mean in data["mean_textbook_circuit_distance"]],
    [std_dev / (2 * math.sqrt(1000)) for std_dev in data["std_textbook_circuit_distance"]],
    label="Textbook Quantum Phase Estimation",
    color="#006f62",
)
plt.errorbar(
    data["bits_precision"],
    [mean / 2 for mean in data["mean_iterative_circuit_distance"]],
    [std_dev / (2 * math.sqrt(1000)) for std_dev in data["std_iterative_circuit_distance"]],
    label="Iterative Quantum Phase Estimation",
    color="#3ccbda",
)

plt.semilogy()
plt.legend()
plt.xlabel("Gridsynth bits of precision")
plt.ylabel("Total variation distance")
plt.savefig("distance.pdf")

gates_fig = plt.figure()

plt.errorbar(
    data["bits_precision"],
    data["mean_textbook_circuit_lengths"],
    data["std_textbook_circuit_lengths"],
    label="Textbook Quantum Phase Estimation",
    color="#006f62",
)
plt.errorbar(
    data["bits_precision"],
    data["mean_iterative_circuit_lengths"],
    data["std_iterative_circuit_lengths"],
    label="Iterative Quantum Phase Estimation",
    color="#3ccbda",
)

plt.legend()
plt.xlabel("Gridsynth bits of precision")
plt.ylabel("Number of gates")
plt.savefig("gates.pdf")

plt.show()
