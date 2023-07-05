# Pauli operation scripts

This folder contains scripts for analysing QASM circuits when implemented as Pauli product rotations,
based on decompositions presented in [A Game of Surface Codes: Large-Scale Quantum Computing with Lattice Surgery](https://doi.org/10.22331/q-2019-03-05-128)
by Daniel Litinski.

- `to_pauli_ops.py` converts a QASM circuit to a collection of Pauli product rotations and measurements. This takes a required argument specifying the QASM circuit to convert to Pauli operations.
- `commute_paulis.py` takes a Pauli rotations file and commutes Clifford and Pauli rotations through the circuit. This takes a required argument specifying the Pauli operations.
- `analyse_pauli_products.py` counts the number of different types of Pauli products in the circuit. This takes a required argument specifying the Pauli operations.
- `analyse_branches.py` counts the lengths of different branches in the case of iterative quantum phase estimation. This takes a required argument specifying the Pauli operations.
