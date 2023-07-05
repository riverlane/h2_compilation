# Lattice surgery operations

This directory contains code for translating QASM circuits to
lattice surgery primitives.

- `to_lattice_operations.py` creates an extended QASM format which includes joint ZZ and XX operations, and decomposes gates like CX into these operations. It takes an optional argument `--qasm_file` which specifies the QASM file to convert to lattice surgery operations. If no file is specified then the file defaults to `circuit_files/qft/first_order/qft_order_1_precision_4.qasm`
- `simulate_lattice_surgery.py` simulates files in this extended QASM format using Qiskit. It takes an optional argument `--eqasm_file` which specifies the extended QASM file containing lattice surgery operations to simulate. If no file is specified then the file defaults to `circuit_files/qft/first_order/qft_order_1_precision_4_ls.eqasm`
