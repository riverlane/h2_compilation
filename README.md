# Supplementary material for "Compilation of a simple chemistry application to quantum error correction primitives"

This repository contains code for generating results presented in the paper ["Compilation of a simple chemistry application to quantum error correction primitives"](https://journals.aps.org/prresearch/abstract/10.1103/PhysRevResearch.6.013325) by Blunt, Gehér, and Moylett.

## Folder structure

- `.devcontainer` and `environment` contain tools for building a Docker environment with the required dependencies.
- `circuit_files` contains QASM circuits for quantum phase estimation.
- `figures` contains figures generated for the paper using this code.
- `logical_circuit` contains code for generating the logical circuit and analysing the Gridsynth decomposition.
- `lattice_operations` contains code for simulating Lattice surgery primitives.
- `pauli_operations` contains code for analysing circuits as Pauli product rotations.
- `resource_estimates` contains code for estimating the resources required for running a QASM circuit.

This repository also contains one submodule from GitHub:
- [`magicstates`](https://github.com/litinski/magicstates) is the supplementary material for [Magic State Distillation: Not as Costly as You Think](https://github.com/litinski/magicstates) by Daniel Litinski. This code was used to estimate the resource requirements for generating $|T\rangle$ states, as used in the `resource_estimates` directory.

When cloning this repository, submodules can be initialised with `git submodule update --init --recursive`.

## Development environment

We include a Dockerfile for an environment with all required dependencies.
If you wish to run the code outside of the development environment, dependencies can be
found in `environment/dev_requirements.txt`.

A Docker container can be built with the command `make build`,
and a shell can be started with the command `make shell`.

## Citation

Nick S. Blunt, György P. Gehér, and Alexandra E. Moylett, Compilation of a simple chemistry application to quantum error correction primitives, Physical Review Research 6, 013325 (2024)

## Notice

(c) Copyright Riverlane 2022-2024. All rights reserved.
