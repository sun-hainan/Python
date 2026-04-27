# -*- coding: utf-8 -*-
"""
算法实现：21_量子计算 / quantum_fourier_transform

本文件实现 quantum_fourier_transform 相关的算法功能。
"""

import numpy as np


class QuantumFourierTransform:
    """
    量子傅里叶变换
    
    电路结构：
    - 对于 n 量子比特：
    - 对每个 qubit i (从 0 开始)：
      - 应用 Hadamard
      - 对每个 qubit j > i，应用 CU1(π/2^{j-i})
    - 最后反转量子比特顺序
    """
    
    def __init__(self, n_qubits):
        self.n = n_qubits
        self.N = 2 ** n_qubits
    
    def hadamard(self):
        """Hadamard 矩阵"""
        return np.array([[1, 1], [1, -1]]) / np.sqrt(2)
    
    def controlled_phase(self, theta):
        """
        受控相位门 CU1(θ)
        
        |00⟩ -> |00⟩
        |01⟩ -> |01⟩
        |10⟩ -> |10⟩
        |11⟩ -> e^{iθ}|11⟩
        """
        return np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, np.exp(1j * theta)]
        ])
    
    def qft_matrix(self):
        """
        构建完整的 QFT 矩阵
        
        QFT_{xy} = (1/√N) e^{2πi xy/N}
        """
        N = self.N
        omega = np.exp(2j * np.pi / N)
        
        indices = np.arange(N)
        outer_sum = np.outer(indices, indices)
        
        qft = omega ** outer_sum / np.sqrt(N)
        
        return qft
    
    def qft_circuit_matrix(self):
        """
        构建量子电路实现的 QFT 矩阵
        
        按照电路结构逐步构建
        """
        n = self.n
        H = self.hadamard()
        
        # 从右到左构建
        circuit = np.eye(2 ** n, dtype=complex)
        
        for target in range(n):
            # 应用 H 到 target
            # 构造单比特 H 的泡利基表示
            dim = 2 ** n
            
            # 简化：使用张量积
            if n == 1:
                circuit = H @ circuit
            else:
                # 构造 H^⊗n @ circuit
                new_circuit = np.zeros((dim, dim), dtype=complex)
                for i in range(dim):
                    for j in range(dim):
                        # 计算 |j⟩ 中 target 位的值
                        bit = (j >> target) & 1
                        if bit == 0:
                            new_circuit[i, j] = circuit[i, j] + circuit[i, j + (1 << target)]
                        else:
                            new_circuit[i, j] = circuit[i, j] - circuit[i, j - (1 << target)]
                new_circuit /= np.sqrt(2)
                circuit = new_circuit
        
        return circuit
    
    def apply_qft(self, state):
        """
        应用 QFT 到状态向量
        
        参数：
            state: 2^n 维状态向量
        
        返回：QFT 后的状态
        """
        qft_mat = self.qft_matrix()
        return qft_mat @ state
    
    def inverse_qft(self, state):
        """
        应用逆 QFT (QFT^\dagger)
        """
        qft_mat = self.qft_matrix()
        return qft_mat.conj().T @ state
    
    def phase_estimation(self, unitary_matrix, precision_qubits):
        """
        相位估计（Quantum Phase Estimation）
        
        参数：
            unitary_matrix: 酉矩阵 U
            precision_qubits: 用于相位精度的量子比特数
        
        返回：特征值的相位
        """
        # 计算特征值
        eigenvalues, eigenvectors = np.linalg.eig(unitary_matrix)
        
        # 取第一个特征向量
        psi0 = eigenvectors[:, 0]
        
        # 相位 = arg(eigenvalue) / (2π)
        phase = np.angle(eigenvalues[0]) / (2 * np.pi)
        
        return phase


def compare_fft_qft(n):
    """
    比较经典 FFT 和量子 QFT 的复杂度
    """
    N = 2 ** n
    
    # 经典 FFT 复杂度
    fft_complexity = N * n
    
    # 量子 QFT 复杂度（门数）
    qft_gates = n * (n + 1) // 2  # n 个 H, n(n-1)/2 个 CU1
    
    return fft_complexity, qft_gates


if __name__ == "__main__":
    print("=" * 55)
    print("量子傅里叶变换（QFT）")
    print("=" * 55)
    
    # QFT 演示
    print("\n1. QFT 矩阵 (n=3)")
    print("-" * 40)
    
    qft = QuantumFourierTransform(3)
    qft_mat = qft.qft_matrix()
    
    print(f"矩阵维度: {qft_mat.shape}")
    print(f"矩阵迹: {np.trace(qft_mat):.4f}")
    
    # 验证酉性
    is_unitary = np.allclose(qft_mat @ qft_mat.conj().T, np.eye(8))
    print(f"是酉矩阵: {is_unitary}")
    
    # 傅里叶基
    print("\n2. 傅里叶基态")
    print("-" * 40)
    
    # |0⟩ -> (1/√N) Σ |k⟩
    state_0 = np.zeros(8, dtype=complex)
    state_0[0] = 1.0
    
    qft_state = qft.apply_qft(state_0)
    
    print(f"|0⟩ 经过 QFT 后的状态幅值:")
    for i, amp in enumerate(qft_state):
        print(f"  |{i}⟩: {amp.real:.4f} + {amp.imag:.4f}i")
    
    # |1⟩ 的变换
    print("\n|1⟩ 经过 QFT 后的状态幅值:")
    state_1 = np.zeros(8, dtype=complex)
    state_1[1] = 1.0
    
    qft_state_1 = qft.apply_qft(state_1)
    for i, amp in enumerate(qft_state_1):
        print(f"  |{i}⟩: {amp.real:.4f} + {amp.imag:.4f}i")
    
    # 复杂度比较
    print("\n3. 复杂度比较")
    print("-" * 40)
    
    print(f"{'n':>4} | {'N=2^n':>6} | {'FFT':>10} | {'QFT门数':>10}")
    print("-" * 40)
    
    for n in [5, 10, 15, 20, 25]:
        N = 2 ** n
        fft_c, qft_c = compare_fft_qft(n)
        print(f"{n:>4} | {N:>6} | {fft_c:>10} | {qft_c:>10}")
