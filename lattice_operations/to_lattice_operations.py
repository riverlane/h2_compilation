# (c) Copyright Riverlane 2022-2023. All rights reserved.

"""
Converts QASM operations to lattice surgery operations.
"""
import argparse
import os

from qiskit import QuantumCircuit

parser = argparse.ArgumentParser()
parser.add_argument(
    "--qasm_file",
    "-q",
    type=str,
    default=os.path.join(
        "circuit_files", "qft", "first_order", "qft_order_1_precision_4.qasm"
    ),
    help="qasm file with instructions to perform.",
)
files = parser.parse_args()

qasm_lines = []
with open(files.qasm_file) as qasm_file:
    for qasm_line in qasm_file:
        if qasm_line.startswith("qreg"):
            # Add extra registers
            qasm_lines.append(qasm_line)
            qasm_lines.append("qreg auxiliary[1];\n")
            qasm_lines.append("creg zz_result[1];\n")
            qasm_lines.append("creg xx_result[1];\n")
            qasm_lines.append("creg auxiliary_result[1];\n")

        elif qasm_line.startswith("z"):
            next_line = next(qasm_file)
            if next_line.startswith("tdg "):
                qubit = qasm_line.split()[1][:-1]

                # Initialise auxiliary
                qasm_lines.append("prep_t auxiliary[0];\n")

                # Measurements
                qasm_lines.append(
                    f"joint_measure z*{qubit} z*auxiliary[0] -> zz_result[0];\n"
                )
                qasm_lines.append(f"measure_x auxiliary[0] -> auxiliary_result[0];\n")

                # Corrections and reset
                qasm_lines.append(f"if (zz_result == 0) s {qubit};\n")
                qasm_lines.append(f"if (zz_result == 1) z {qubit};\n")
                qasm_lines.append(f"if (auxiliary_result == 1) z {qubit};\n")
                qasm_lines.append(f"if (auxiliary_result == 1) x auxiliary[0];\n")

            elif next_line.startswith("t "):
                qubit = qasm_line.split()[1][:-1]

                # Initialise auxiliary
                qasm_lines.append("prep_t auxiliary[0];\n")

                # Measurements
                qasm_lines.append(
                    f"joint_measure z*{qubit} z*auxiliary[0] -> zz_result[0];\n"
                )
                qasm_lines.append(f"measure_x auxiliary[0] -> auxiliary_result[0];\n")

                # Corrections and reset
                qasm_lines.append(f"if (zz_result == 1) sdg {qubit};\n")
                qasm_lines.append(f"if (zz_result == 0) z {qubit};\n")
                qasm_lines.append(f"if (auxiliary_result == 1) z {qubit};\n")
                qasm_lines.append(f"if (auxiliary_result == 1) x auxiliary[0];\n")
            else:
                qasm_lines.append(qasm_line)
                qasm_lines.append(next_line)

        elif qasm_line.startswith("cx"):
            q_control, q_target = qasm_line[3:-2].split(",")

            # Initialise auxiliary
            qasm_lines.append("prep_x auxiliary[0];\n")

            # Joint ZZ measurement
            qasm_lines.append(
                f"joint_measure z*{q_control} z*auxiliary[0] -> zz_result[0];\n"
            )

            # Joint XX measurement
            qasm_lines.append(
                f"joint_measure x*{q_target} x*auxiliary[0] -> xx_result[0];\n"
            )

            # Measure auxiliary
            qasm_lines.append("measure auxiliary[0] -> auxiliary_result[0];\n")

            # Corrections
            qasm_lines.append(f"if (xx_result==1) z {q_control};\n")
            qasm_lines.append(f"if (zz_result==1) x {q_target};\n")
            qasm_lines.append(f"if (auxiliary_result==1) x {q_target};\n")
            qasm_lines.append("if (auxiliary_result==1) x auxiliary[0];\n")

        elif qasm_line.startswith("s "):
            qubit = qasm_line.split()[1][:-1]

            # Initialise auxiliary
            qasm_lines.append("prep_y auxiliary[0];\n")

            # Measurements
            qasm_lines.append(
                f"joint_measure z*{qubit} z*auxiliary[0] -> zz_result[0];\n"
            )
            qasm_lines.append(f"measure_x auxiliary[0] -> auxiliary_result[0];\n")

            # Corrections and reset
            qasm_lines.append(f"if (zz_result == 1) z {qubit};\n")
            qasm_lines.append(f"if (auxiliary_result == 1) z {qubit};\n")
            qasm_lines.append(f"if (auxiliary_result == 1) x auxiliary[0];\n")

        elif qasm_line.startswith("sdg "):
            qubit = qasm_line.split()[1][:-1]

            # Initialise auxiliary
            qasm_lines.append("prep_y auxiliary[0];\n")

            # Measurements
            qasm_lines.append(
                f"joint_measure z*{qubit} z*auxiliary[0] -> zz_result[0];\n"
            )
            qasm_lines.append(f"measure_x auxiliary[0] -> auxiliary_result[0];\n")

            # Corrections and reset
            qasm_lines.append(f"if (zz_result == 0) z {qubit};\n")
            qasm_lines.append(f"if (auxiliary_result == 1) z {qubit};\n")
            qasm_lines.append(f"if (auxiliary_result == 1) x auxiliary[0];\n")

        elif qasm_line.startswith("t "):
            qubit = qasm_line.split()[1][:-1]

            # Initialise auxiliary
            qasm_lines.append("prep_t auxiliary[0];\n")

            # Measurements
            qasm_lines.append(
                f"joint_measure z*{qubit} z*auxiliary[0] -> zz_result[0];\n"
            )
            qasm_lines.append(f"measure_x auxiliary[0] -> auxiliary_result[0];\n")

            # Corrections and reset
            qasm_lines.append(f"if (zz_result == 1) s {qubit};\n")
            qasm_lines.append(f"if (auxiliary_result == 1) z {qubit};\n")
            qasm_lines.append(f"if (auxiliary_result == 1) x auxiliary[0];\n")

        elif qasm_line.startswith("tdg "):
            qubit = qasm_line.split()[1][:-1]

            # Initialise auxiliary
            qasm_lines.append("prep_t auxiliary[0];\n")

            # Measurements
            qasm_lines.append(
                f"joint_measure z*{qubit} z*auxiliary[0] -> zz_result[0];\n"
            )
            qasm_lines.append(f"measure_x auxiliary[0] -> auxiliary_result[0];\n")

            # Corrections and reset
            qasm_lines.append(f"if (zz_result == 0) sdg {qubit};\n")
            qasm_lines.append(f"if (auxiliary_result == 1) z {qubit};\n")
            qasm_lines.append(f"if (auxiliary_result == 1) x auxiliary[0];\n")

        else:
            qasm_lines.append(qasm_line)

qasm_str = "".join(qasm_lines)

# Get the filename with the extension stripped
filename_root = files.qasm_file[: files.qasm_file.index(".")]
eqasm_filename = filename_root + "_ls.eqasm"

with open(eqasm_filename, "w") as qasm_output:
    qasm_output.write(qasm_str)
