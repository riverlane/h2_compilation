# (c) Copyright Riverlane 2022-2024. All rights reserved.

import sys
from typing import Dict, List, TextIO, Tuple

IS_ITERATIVE = "iqpe" in sys.argv[1]


def write_condition(condition):
    if condition == "":
        return ""
    else:
        return "&&".join(
            [f"({cindex}=={value})" for cindex, value in condition.items()]
        )


def write_instruction(
    pauli_file: TextIO,
    num_qubits: int,
    rotations: List[Tuple[int, str]],
    instruction: str = "rotate",
    angle: int = "",
    cindex: int = "",
    condition: Dict[int, int] = "",
):
    """Write instruction to the CSV file as the following format:
    - Type of instruction (rotate or measure)
    - Angle specified by an integer n, where the corresponding rotation angle is pi/n
    - Pauli for each qubit (I, X, Y or Z)
    - Classical bit index (used for measurement or conditions)
    - Classical bit value (used for conditional operation)

    Parameters
    ----------
    pauli_file : TextIO
        CSV file to write the instruction to
    num_qubits : int
        Number of qubits
    rotations : List[Tuple[int, str]]
        Paulis involved in the rotation, as qubit index and basis
    instruction : str, optional
        Type of instruction ("rotate" or "measure"),
        by default "rotate"
    angle : int, optional
        Angle specified by an integer n, where the corresponding
        rotation angle is pi/n, by default ""
    cindex : int, optional
        Classical bit index, by default ""
    condition : Dict[int, int], optional
        Pair of classical bit index and value for condition, by default "".
    """
    joint = ["i" for _ in range(num_qubits)]
    for index, basis in rotations:
        joint[index] = basis
    pauli_file.write(
        f"{instruction},{angle},{','.join(joint)},{cindex},{write_condition(condition)}\n"
    )


def get_index(string: str, is_measurement_cbit: bool = False) -> int:
    """Get the index of the quantum or classical bit from the QASM string.

    In QASM, variables are registers written as q0[i] or cn[i].
    The value we want is usually i, hence we split according to the
    square brackets to get the value i.

    Note however that in some circumstances (eg IQPE) the index is actually n.
    This is because in IQPE we want to do conditional operations,
    and QASM/Qiskit do not allow us to condition on indexes of a classical register.
    To identify when to do this, we check if we're parsing a classical variable in
    an IQPE circuit and if so select n instead.

    Parameters
    ----------
    string : str
        The variable or QASM string containing the variable
    is_measurement_cbit : bool, optional
        Used to determine if we need to return n or i
        depending on if we're getting a classical index
        in an IQPE circuit, by default False

    Returns
    -------
    int
        Index of the quantum or classical register
    """
    if "[" in string:
        parsed = string.split("[")
        if is_measurement_cbit and IS_ITERATIVE:
            return int(parsed[0][1:])
        else:
            return int(parsed[1].split("]")[0])
    else:
        return int(string[1:])


def parse_instruction(
    pauli_file: TextIO,
    num_qubits: int,
    line: str,
    condition: Dict[int, int] = "",
):
    """Parse an instruction into Pauli rotations and write it to the CSV file.

    Parameters
    ----------
    pauli_file : TextIO
        CSV file for the Pauli rotations.
    num_qubits : int
        Number of qubits.
    line : str
        QASM line.
    condition : Dict[int, int], optional
        Pair of classical bit index and value for condition, by default "".

    Raises
    ------
    ValueError
        Raised if the instruction is not supported.
    """
    if line.startswith("x"):
        index = get_index(line)
        write_instruction(
            pauli_file,
            num_qubits,
            [(index, "x")],
            angle=2,
            condition=condition,
        )
    elif line.startswith("z"):
        index = get_index(line)
        write_instruction(
            pauli_file,
            num_qubits,
            [(index, "z")],
            angle=2,
            condition=condition,
        )
    elif line.startswith("s"):
        index = get_index(line)
        write_instruction(
            pauli_file,
            num_qubits,
            [(index, "z")],
            angle=4,
            condition=condition,
        )
    elif line.startswith("sdg"):
        index = get_index(line)
        write_instruction(
            pauli_file,
            num_qubits,
            [(index, "z")],
            angle=-4,
            condition=condition,
        )
    elif line.startswith("h"):
        # Decompose Hadamard into three pi/4 rotations (XZX)
        index = get_index(line)
        write_instruction(
            pauli_file,
            num_qubits,
            [(index, "x")],
            angle=4,
            condition=condition,
        )
        write_instruction(
            pauli_file,
            num_qubits,
            [(index, "z")],
            angle=4,
            condition=condition,
        )
        write_instruction(
            pauli_file,
            num_qubits,
            [(index, "x")],
            angle=4,
            condition=condition,
        )
    elif line.startswith("t"):
        index = get_index(line)
        write_instruction(
            pauli_file,
            num_qubits,
            [(index, "z")],
            angle=8,
            condition=condition,
        )
    elif line.startswith("tdg"):
        index = get_index(line)
        write_instruction(
            pauli_file, num_qubits, [(index, "z")], angle=-8, condition=condition
        )
    elif line.startswith("cx"):
        # Decompose CX into a joint pi/4 ZX rotation and -pi/4 Z and X rotations.
        qubits = line[3:-2].split(",")
        control = get_index(qubits[0])
        target = get_index(qubits[1])
        write_instruction(
            pauli_file,
            num_qubits,
            [(control, "z"), (target, "x")],
            angle=4,
            condition=condition,
        )
        write_instruction(
            pauli_file,
            num_qubits,
            [(control, "z")],
            angle=-4,
            condition=condition,
        )
        write_instruction(
            pauli_file,
            num_qubits,
            [(target, "x")],
            angle=-4,
            condition=condition,
        )
    elif line.startswith("measure"):
        qubit, cbit = line.split(" -> ")
        qindex = get_index(qubit)
        cindex = get_index(cbit, True)
        write_instruction(
            pauli_file,
            num_qubits,
            [(qindex, "z")],
            instruction="measure",
            cindex=cindex,
            condition=condition,
        )
    else:
        raise ValueError(line)


if __name__ == "__main__":
    with open(sys.argv[1]) as qasm_file:
        pauli_operations = []

        if qasm_file.readline().startswith("//"):
            # Skipping copyright notice
            next(qasm_file)
            next(qasm_file)
        next(qasm_file)
        with open(
            f"{'.'.join(sys.argv[1].split('.')[:-1])}_paulis.csv", "w"
        ) as pauli_file:
            for line in qasm_file:
                if line.startswith("qreg"):
                    num_qubits = get_index(line)
                elif line.startswith("creg"):
                    pass
                elif line.startswith("if"):
                    parts = line.split(") ")
                    condition = parts[0].split("(")[1]
                    cbit, value = condition.split("==")
                    cindex = get_index(cbit)
                    parse_instruction(
                        pauli_file, num_qubits, parts[1], {cindex: int(value)}
                    )
                else:
                    parse_instruction(pauli_file, num_qubits, line)
