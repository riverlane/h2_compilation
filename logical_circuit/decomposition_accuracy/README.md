# Decomposition accuracy scripts

This folder contains scripts for analysing the trade-off between
overall accuracy and number of gates depending on the precision
of `gridsynth` decompositions.

- `decomposition_accuracy.py` produces the mean and standard deviation of the total variation distance and number of gates for differing bits of precision.
- `plot_decomposition_accuracy.py` produces the figures used in the paper.
- `gate_counts.py` takes a fixed gridsynth precision and presents the number of different types of gates for different randomly generated circuits.
