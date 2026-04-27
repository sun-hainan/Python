# -*- coding: utf-8 -*-
"""
算法实现：量子机器学习 / qml_basics

本文件实现 qml_basics 相关的算法功能。
"""

import numpy as np
from typing import List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum


class Quantum_State(Enum):
    """量子计算基态"""
    ZERO = np.array([1.0, 0.0])   # |0>
    ONE = np.array([0.0, 1.0])    # |1>


@dataclass
class Qubit:
    """量子比特"""
    state: np.ndarray  # 2维复数向量 [α, β]，|ψ> = α|0> + β|1>


class Quantum_Circuit:
    """量子电路（简化实现）"""
    def __init__(self, num_qubits: int):
        self.num_qubits = num_qubits
        # 初始态 |00...0>
        self.state = np.zeros(2 ** num_qubits, dtype=complex)
        self.state[0] = 1.0 + 0j


    def apply_gate(self, gate: np.ndarray, target_qubit: int, controls: List[int] = None):
        """应用量子门到目标量子比特"""
        if controls is None:
            # 单量子比特门
            full_gate = self._expand_gate(gate, target_qubit)
        else:
            # 多量子比特门（控制门）
            full_gate = self._expand_controlled_gate(gate, target_qubit, controls)
        self.state = full_gate @ self.state


    def _expand_gate(self, gate: np.ndarray, target_qubit: int) -> np.ndarray:
        """将单量子比特门扩展到整个系统"""
        dim = 2 ** self.num_qubits
        result = np.eye(dim, dtype=complex)
        # 计算门应用的位置
        for i in range(dim):
            # 检查target_qubit对应的位
            if (i >> target_qubit) & 1:
                # 需要应用门
                pass
        # 简化：使用张量积构建
        # I ⊗ ... ⊗ gate ⊗ ... ⊗ I
        from functools import reduce
        gates = []
        for i in range(self.num_qubits):
            if i == target_qubit:
                gates.append(gate)
            else:
                gates.append(np.eye(2, dtype=complex))
        result = reduce(np.kron, gates)
        return result


    def _expand_controlled_gate(self, gate: np.ndarray, target: int, controls: List[int]) -> np.ndarray:
        """构建控制门矩阵"""
        dim = 2 ** self.num_qubits
        result = np.eye(dim, dtype=complex)
        # 简化：构建CU门
        # 对于每个基态，如果控制位都为1，则应用gate到目标
        for i in range(dim):
            # 检查控制位
            controls_satisfied = all(((i >> c) & 1) for c in controls)
            target_bit = (i >> target) & 1
            # 计算目标索引
            if controls_satisfied:
                # 应用gate
                new_target_bit = int(gate[1, 1]) if target_bit else int(gate[0, 1]) if gate.shape[0] > 1 else target_bit
        return result


    def measure(self) -> int:
        """测量整个量子系统（返回整数）"""
        # 概率幅的平方得到概率
        probabilities = np.abs(self.state) ** 2
        # 归一化
        probabilities /= probabilities.sum()
        # 采样
        result = np.random.choice(len(probabilities), p=probabilities)
        return result


    def measure_qubit(self, qubit_idx: int) -> int:
        """测量指定量子比特"""
        # 计算指定量子比特的密度矩阵
        # 简化：直接测量
        dim = 2 ** self.num_qubits
        probs = np.zeros(2)
        for i in range(dim):
            if (i >> qubit_idx) & 1:
                probs[1] += np.abs(self.state[i]) ** 2
            else:
                probs[0] += np.abs(self.state[i]) ** 2
        probs /= probs.sum()
        return np.random.choice(2, p=probs)


    def get_expectation(self, observable: np.ndarray) -> float:
        """计算可观测量期望值 <ψ|O|ψ>"""
        return np.vdot(self.state, observable @ self.state).real


class Basic_Quantum_Gates:
    """基本量子门"""
    # Pauli X (NOT门)
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    # Pauli Y
    Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    # Pauli Z
    Z = np.array([[1, 0], [0, -1]], dtype=complex)
    # Hadamard
    H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
    # S门（相位门）
    S = np.array([[1, 0], [0, 1j]], dtype=complex)
    # T门
    T = np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex)
    # CNOT
    CNOT = np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0]
    ], dtype=complex)


class Parameterized_Quantum_Circuit:
    """参数化量子电路（PQC）"""
    def __init__(self, num_qubits: int, depth: int = 2):
        self.num_qubits = num_qubits
        self.depth = depth
        self.parameters: List[float] = []
        self.gates_sequence: List[Tuple[str, int, float]] = []  # (gate_type, qubit, param_idx)


    def add_rotations(self):
        """添加参数化旋转门"""
        # 每层添加 Ry 和 Rz 旋转
        for d in range(self.depth):
            for q in range(self.num_qubits):
                self.gates_sequence.append(('RY', q, len(self.parameters)))
                self.parameters.append(np.random.uniform(0, 2 * np.pi))
                self.gates_sequence.append(('RZ', q, len(self.parameters)))
                self.parameters.append(np.random.uniform(0, 2 * np.pi))


    def build_circuit(self, params: List[float] = None) -> Quantum_Circuit:
        """构建量子电路"""
        if params is None:
            params = self.parameters
        circuit = Quantum_Circuit(self.num_qubits)
        for gate_type, qubit, param_idx in self.gates_sequence:
            angle = params[param_idx]
            if gate_type == 'RY':
                gate = self._ry_gate(angle)
            elif gate_type == 'RZ':
                gate = self._rz_gate(angle)
            elif gate_type == 'RX':
                gate = self._rx_gate(angle)
            circuit.apply_gate(gate, qubit)
        return circuit


    def _ry_gate(self, theta: float) -> np.ndarray:
        """Ry旋转门"""
        return np.array([
            [np.cos(theta / 2), -np.sin(theta / 2)],
            [np.sin(theta / 2), np.cos(theta / 2)]
        ], dtype=complex)


    def _rz_gate(self, theta: float) -> np.ndarray:
        """Rz旋转门"""
        return np.array([
            [np.exp(-1j * theta / 2), 0],
            [0, np.exp(1j * theta / 2)]
        ], dtype=complex)


    def _rx_gate(self, theta: float) -> np.ndarray:
        """Rx旋转门"""
        return np.array([
            [np.cos(theta / 2), -1j * np.sin(theta / 2)],
            [-1j * np.sin(theta / 2), np.cos(theta / 2)]
        ], dtype=complex)


    def forward(self, params: List[float], observable: np.ndarray = None) -> float:
        """前向传播：执行电路并计算期望值"""
        circuit = self.build_circuit(params)
        if observable is None:
            # 默认测量第一个量子比特在Z基态
            observable = np.diag([1, -1])
        return circuit.get_expectation(observable)


def bell_state_preparation() -> Quantum_Circuit:
    """制备Bell态 |Φ+> = (|00> + |11>)/√2"""
    circuit = Quantum_Circuit(2)
    # 应用Hadamard到第一个量子比特
    circuit.apply_gate(Basic_Quantum_Gates.H, 0)
    # 应用CNOT
    circuit.apply_gate(Basic_Quantum_Gates.CNOT, 1, controls=[0])
    return circuit


def ghz_state_preparation(num_qubits: int) -> Quantum_Circuit:
    """制备GHZ态 |GHZ> = (|00...0> + |11...1>)/√2"""
    circuit = Quantum_Circuit(num_qubits)
    # 应用Hadamard
    circuit.apply_gate(Basic_Quantum_Gates.H, 0)
    # 应用CNOT链
    for i in range(num_qubits - 1):
        circuit.apply_gate(Basic_Quantum_Gates.CNOT, i + 1, controls=[i])
    return circuit


def basic_test():
    """基本功能测试"""
    print("=== 量子机器学习基础测试 ===")
    # 测试单量子比特
    print("\n[单量子比特操作]")
    qubit = Qubit(state=Quantum_State.ZERO.value.copy())
    print(f"初始态 |0>: {qubit.state}")
    # 应用Hadamard
    circuit = Quantum_Circuit(1)
    circuit.apply_gate(Basic_Quantum_Gates.H, 0)
    print(f"应用H后: {circuit.state}")
    # 测量
    measurement_results = [circuit.measure_qubit(0) for _ in range(100)]
    ones_count = sum(measurement_results)
    print(f"测量100次: |0>出现{100 - ones_count}次, |1>出现{ones_count}次")
    # 测试Bell态
    print("\n[Bell态制备]")
    bell = bell_state_preparation()
    print(f"Bell态向量: {bell.state}")
    # 测量
    measurements = [bell.measure() for _ in range(50)]
    states = {}
    for m in measurements:
        s = format(m, f'0{2}b')
        states[s] = states.get(s, 0) + 1
    print(f"测量结果分布: {states}")
    # 测试参数化量子电路
    print("\n[参数化量子电路]")
    pqc = Parameterized_Quantum_Circuit(num_qubits=2, depth=2)
    pqc.add_rotations()
    print(f"参数数量: {len(pqc.parameters)}")
    # 执行PQC
    result = pqc.forward(pqc.parameters)
    print(f"期望值: {result:.4f}")


if __name__ == "__main__":
    basic_test()
