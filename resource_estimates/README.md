# Resource estimates

This folder contains a script for estimating the resources required for running an iterative QPE QASM circuit.

- `estimate_resources.py` estimates the resources required for implementing iterative QPE on the surface code. This takes a required argument specifying the QASM circuit whose resources we want to estimate.
- `factory_resources.csv` contains resource requirements for different $|T\rangle$ factories, based on numbers gathered from running code Daniel Litinski created for [Magic State Distillation: Not as Costly as You Think](https://quantum-journal.org/papers/q-2019-12-02-205/). This code is available in the directory `magicstates`.
