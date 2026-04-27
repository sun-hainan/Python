# -*- coding: utf-8 -*-
"""
算法实现：21_量子计算 / stabilizer_formalism

本文件实现 stabilizer_formalism 相关的算法功能。
"""

import numpy as np
from collections import defaultdict


class StabilizerState:
    """
    稳定子态
    
    稳定子（Stabilizer）是保护量子态的算符集合
    
    对于 n 量子比特态 |ψ⟩：
    - 稳定子是满足 G|ψ⟩ = |ψ⟩ 的算符 G 的集合
    - 可以用 n 个独立生成元描述
    
    表示：
    - 使用 Pauli 矩阵的线性组合
    - 通过表格（tableau）表示
    """
    
    def __init__(self, n):
        self.n = n  # 量子比特数
        
        # 稳定子表格表示
        # 每行：[x[0..n-1], z[0..n-1], phase]
        # x[i], z[i] 表示第 i 个量子比特的 Pauli
        # phase: 0=+1, 1=+i, 2=-1, 3=-i
        
        # 初始态 |00...0⟩ 的稳定子
        self.stabilizers = []  # list of (x, z, phase)
        
        for i in range(n):
            x = [0] * n
            z = [0] * n
            x[i] = 1  # X_i
            self.stabilizers.append((x, z, 0))  # +X_i
    
    def apply_hadamard(self, qubit):
        """应用 H 门到量子比特"""
        for i in range(len(self.stabilizers)):
            x, z, phase = self.stabilizers[i]
            # H: X <-> Z
            x[qubit], z[qubit] = z[qubit], x[qubit]
            self.stabilizers[i] = (x, z, phase)
    
    def apply_s(self, qubit):
        """应用 S 门（Phase gate）到量子比特"""
        for i in range(len(self.stabilizers)):
            x, z, phase = self.stabilizers[i]
            # S: Z -> Z, X -> Y = iXZ
            if x[qubit] == 1 and z[qubit] == 0:
                z[qubit] = 1
                phase = (phase + 1) % 4  # +i
            elif x[qubit] == 1 and z[qubit] == 1:
                x[qubit] = 0
                z[qubit] = 1
                phase = (phase + 3) % 4  # -i
            self.stabilizers[i] = (x, z, phase)
    
    def apply_cnot(self, control, target):
        """应用 CNOT 门"""
        for i in range(len(self.stabilizers)):
            x, z, phase = self.stabilizers[i]
            # CNOT: 
            # control: X_c -> X_c X_t, Z_c -> Z_c
            # target: X_t -> X_t, Z_t -> Z_c Z_t
            if x[control] == 1:
                x[target] = (x[target] + 1) % 2
                phase = (phase + x[target] * z[control]) % 4
            if z[target] == 1:
                z[control] = (z[control] + 1) % 2
            self.stabilizers[i] = (x, z, phase)
    
    def apply_pauli(self, pauli_string):
        """
        应用 Pauli 门串
        pauli_string: 如 'XYZI' 表示 X⊗Y⊗Z⊗I
        """
        for i in range(len(self.stabilizers)):
            x, z, phase = self.stabilizers[i]
            for q, p in enumerate(pauli_string):
                if p == 'X':
                    x[q] = (x[q] + 1) % 2
                elif p == 'Y':
                    x[q] = (x[q] + 1) % 2
                    z[q] = (z[q] + 1) % 2
                elif p == 'Z':
                    z[q] = (z[q] + 1) % 2
            self.stabilizers[i] = (x, z, phase)
    
    def measure(self, qubit):
        """
        测量量子比特
        
        返回：测量结果 (0 或 1)
        """
        # 找到包含 X 或 Y 在该量子比特上的稳定子
        MeasZ = [0] * self.n  # 用于测量的 Z
        MeasZ[qubit] = 1
        
        # 高斯消元找到秩
        stabilizer_copy = [s for s in self.stabilizers]
        
        # 简化：返回随机结果
        result = np.random.randint(0, 2)
        
        # 更新稳定子
        if result == 0:
            # 结果为 0，保持当前稳定子
            pass
        else:
            # 结果为 1，需要更新
            # 简化：翻转某个相关量子比特
            pass
        
        return result
    
    def expectation_value(self, observable):
        """
        计算可观测量 ⟨ψ|O|ψ⟩
        
        参数：
            observable: Pauli 字符串，如 'XYZI'
        """
        # 简化：计算稳定子与可观测量是否对易
        n = len(observable)
        
        # 检查是否所有稳定子都与 observable 对易
        commutes = True
        for x, z, phase in self.stabilizers:
            anticommutes = False
            for i in range(n):
                if observable[i] == 'I':
                    continue
                if observable[i] == 'X' and x[i] == 1:
                    anticommutes = not anticommutes
                elif observable[i] == 'Y':
                    if x[i] == 1 or z[i] == 1:
                        anticommutes = not anticommutes
                elif observable[i] == 'Z' and z[i] == 1:
                    anticommutes = not anticommutes
            
            if anticommutes:
                commutes = False
                break
        
        if commutes:
            # 对易，返回 +1 或 -1
            return 1.0
        else:
            # 不对易，随机
            return np.random.choice([1, -1])
    
    def print_stabilizers(self):
        """打印稳定子"""
        pauli_map = {0: 'I', 1: 'X', 2: 'Y', 3: 'Z'}
        phase_map = {0: '+', 1: '+i', 2: '-', 3: '-i'}
        
        print("\n稳定子生成元：")
        for i, (x, z, phase) in enumerate(self.stabilizers):
            pauli_str = ''
            for j in range(self.n):
                idx = x[j] + 2 * z[j]
                pauli_str += pauli_map[idx]
            print(f"  {phase_map[phase]} {pauli_str}")


def clifford_circuit_simulation(n, gates):
    """
    Clifford 电路模拟
    
    参数：
        n: 量子比特数
        gates: 门列表 [(gate_type, qubits), ...]
              gate_type: 'H', 'S', 'CNOT', 'X', 'Y', 'Z'
    """
    state = StabilizerState(n)
    
    print(f"初始态 |{'0' * n}⟩ 的稳定子：")
    state.print_stabilizers()
    
    print(f"\n应用 {len(gates)} 个门：")
    
    for gate_type, qubits in gates:
        if gate_type == 'H':
            state.apply_hadamard(qubits[0])
            print(f"  H({qubits[0]})")
        elif gate_type == 'S':
            state.apply_s(qubits[0])
            print(f"  S({qubits[0]})")
        elif gate_type == 'CNOT':
            state.apply_cnot(qubits[0], qubits[1])
            print(f"  CNOT({qubits[0]}, {qubits[1]})")
        elif gate_type in ['X', 'Y', 'Z']:
            pauli = gate_type + 'I' * (qubits[0]) + 'I' * (n - qubits[0] - 1)
            # 简化：只翻转对应量子比特
            x = [0] * n
            z = [0] * n
            if gate_type == 'X':
                x[qubits[0]] = 1
            elif gate_type == 'Y':
                x[qubits[0]] = 1
                z[qubits[0]] = 1
            elif gate_type == 'Z':
                z[qubits[0]] = 1
            for i in range(n):
                sx, sz, sp = state.stabilizers[i]
                sx[qubits[0]] = x[qubits[0]]
                sz[qubits[0]] = z[qubits[0]]
                state.stabilizers[i] = (sx, sz, sp)
            print(f"  {gate_type}({qubits[0]})")
    
    print("\n最终稳定子：")
    state.print_stabilizers()
    
    return state


if __name__ == "__main__":
    print("=" * 55)
    print("稳定子形式（Stabilizer Formalism）")
    print("=" * 55)
    
    # 示例：Bell 态制备
    print("\n1. Bell 态 (|00⟩ + |11⟩)/√2 的稳定子")
    print("-" * 40)
    
    n = 2
    state = StabilizerState(n)
    
    # 电路：H(0) -> CNOT(0,1)
    gates = [
        ('H', [0]),
        ('CNOT', [0, 1]),
    ]
    
    clifford_circuit_simulation(n, gates)
    
    # 可观测量期望值
    print("\n2. 可观测量期望值")
    print("-" * 40)
    
    # |ψ⟩ = (|00⟩ + |11⟩)/√2
    # ⟨XX⟩ = ⟨YY⟩ = ⟨ZZ⟩ = 1
    # ⟨XI⟩ = ⟨IZ⟩ = 0
    
    test_obs = ['XI', 'IZ', 'XX', 'YY', 'ZZ']
    for obs in test_obs:
        val = state.expectation_value(obs)
        print(f"  ⟨{obs}⟩ = {val}")
    
    # GHZ 态示例
    print("\n3. GHZ 态 (|000⟩ + |111⟩)/√2")
    print("-" * 40)
    
    n = 3
    ghz_state = StabilizerState(n)
    
    ghz_gates = [
        ('H', [0]),
        ('CNOT', [0, 1]),
        ('CNOT', [0, 2]),
    ]
    
    clifford_circuit_simulation(n, ghz_gates)
