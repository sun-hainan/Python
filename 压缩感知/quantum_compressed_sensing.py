# -*- coding: utf-8 -*-
"""
算法实现：压缩感知 / quantum_compressed_sensing

本文件实现 quantum_compressed_sensing 相关的算法功能。
"""

import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class QubitState:
    """量子比特状态"""
    # 状态向量 |ψ⟩ = α|0⟩ + β|1⟩，存储为 [α, β]
    amplitudes: np.ndarray  # shape: (2,)


class QuantumCompressiveSampling:
    """
    量子压缩采样框架（简化模拟）
    假设：
    1. 经典信号 x 可以编码为量子态 |x⟩
    2. 测量可以表示为量子演化
    3. 多测量可以并行执行（量子叠加）
    """

    def __init__(self, n: int, m: int):
        self.n = n  # 信号维度
        self.m = m  # 测量数
        self.num_qubits = int(np.ceil(np.log2(n)))  # 所需量子比特数

    def encode_classical_signal(self, x: np.ndarray) -> QubitState:
        """
        将经典信号编码为量子态
        |x⟩ = Σ_i x_i |i⟩ / ||x||
        """
        norm = np.linalg.norm(x)
        if norm < 1e-10:
            return QubitState(amplitudes=np.array([1.0, 0.0]))

        amplitudes = x / norm
        # 填充到2^n维度
        if len(amplitudes) < 2 ** self.num_qubits:
            padded = np.zeros(2 ** self.num_qubits)
            padded[:len(amplitudes)] = amplitudes
            amplitudes = padded

        return QubitState(amplitudes=amplitudes)

    def quantum_measurement(self, state: QubitState,
                          basis: np.ndarray) -> np.ndarray:
        """
        量子测量（模拟）
        在指定基下测量量子态
        返回测量结果（经典向量）
        """
        # 简化：直接返回振幅的某种组合
        # 实际需要密度矩阵和POVM
        return np.abs(state.amplitudes[:self.m])

    def quantum_sampling(self, x: np.ndarray) -> np.ndarray:
        """
        量子压缩采样
        原理：通过量子态编码，利用测量提取信息
        """
        # 编码为量子态
        qstate = self.encode_classical_signal(x)

        # 量子测量
        measurements = self.quantum_measurement(qstate, np.eye(self.m))

        return measurements


class QuantumIterativeThresholding:
    """
    量子迭代阈值算法（QIST）
    经典IHT的量子版本
    """

    def __init__(self, n: int, m: int):
        self.n = n
        self.m = m
        self.A = np.random.randn(m, n) / np.sqrt(m)  # 测量矩阵（经典模拟）

    def q_amp(self, x: np.ndarray) -> np.ndarray:
        """量子振幅放大（Grover迭代的简化模拟）"""
        # 简化的振幅放大：增强目标状态
        x_norm = np.linalg.norm(x)
        if x_norm < 1e-10:
            return x

        # 翻转最小幅度的比特（Grover oracle的简化）
        x_flipped = x.copy()
        min_idx = np.argmin(np.abs(x))
        x_flipped[min_idx] = -x_flipped[min_idx]

        # 扩散算子（简化）
        x_diffused = -x_flipped + 2 * x.mean()

        return x_diffused

    def q_ist(self, y: np.ndarray, s: int,
              max_iter: int = 100) -> np.ndarray:
        """
        量子IST算法
        """
        x = np.zeros(self.n)

        for _ in range(max_iter):
            # 梯度步骤
            residual = y - self.A @ x
            gradient = self.A.T @ residual

            # 量子加速步骤（振幅放大）
            x_new = x + gradient
            x_new = self._quantum_amp_amplify(x_new, target_amplitude=s)

            # 硬阈值
            magnitudes = np.abs(x_new)
            threshold_idx = np.argsort(magnitudes)[-s:]
            x = np.zeros(self.n)
            x[threshold_idx] = x_new[threshold_idx]

        return x

    def _quantum_amp_amplify(self, x: np.ndarray, target_amplitude: int) -> np.ndarray:
        """
        振幅放大（Quantum Amplitude Amplification）
        简化版：通过迭代增强目标分量的幅度
        """
        x_norm = np.linalg.norm(x)
        if x_norm < 1e-10:
            return x

        # 获取目标索引（大幅度的分量）
        sorted_idx = np.argsort(np.abs(x))
        target_idx = sorted_idx[-target_amplitude:]

        # 振幅放大：增强目标，减少非目标
        x_amplified = x.copy()
        for i in range(len(x)):
            if i in target_idx:
                x_amplified[i] *= 1.5  # 增强因子
            else:
                x_amplified[i] *= 0.8  # 衰减因子

        # 重新归一化
        x_amplified = x_amplified / np.linalg.norm(x_amplified) * x_norm

        return x_amplified


class QuantumCorrelationDetector:
    """
    量子相关性检测（Quantum Correlation Detector）
    用于检测量子态之间的相关性
    """

    @staticmethod
    def fidelity(state1: QubitState, state2: QubitState) -> float:
        """
        计算两个量子态的保真度
        F = |⟨ψ1|ψ2⟩|²
        """
        inner_prod = np.vdot(state1.amplitudes, state2.amplitudes)
        return np.abs(inner_prod) ** 2

    @staticmethod
    def entanglement_measure(state: QubitState) -> float:
        """
        纠缠度量（简化：使用状态向量的范数熵）
        """
        probs = np.abs(state.amplitudes) ** 2
        probs = probs[probs > 1e-10]  # 去除零
        entropy = -np.sum(probs * np.log2(probs))
        return entropy


def test_quantum_cs():
    """测试量子压缩感知"""
    np.random.seed(42)

    n = 256  # 信号维度
    m = 64   # 测量数
    s = 20   # 稀疏度

    print("=== 量子压缩感知测试 ===")
    print(f"信号维度: {n}, 测量数: {m}, 稀疏度: {s}")
    print(f"所需量子比特: {int(np.ceil(np.log2(n)))}")

    # 生成稀疏信号
    x_true = np.zeros(n)
    support = np.random.choice(n, s, replace=False)
    x_true[support] = np.random.randn(s)

    # 量子压缩采样
    qcs = QuantumCompressiveSampling(n, m)
    measurements = qcs.quantum_sampling(x_true)

    print(f"\n测量结果（量子采样）:")
    print(f"  测量维度: {len(measurements)}")
    print(f"  总能量: {np.sum(measurements**2):.4f}")

    # 量子IST恢复
    print("\n--- 量子IST恢复 ---")
    qist = QuantumIterativeThresholding(n, m)
    x_recovered = qist.q_ist(measurements, s)

    error = np.linalg.norm(x_recovered - x_true) / np.linalg.norm(x_true)
    print(f"恢复误差: {error:.6f}")

    # 量子态保真度测试
    print("\n--- 量子态操作测试 ---")
    qstate = qcs.encode_classical_signal(x_true)
    print(f"量子态振幅数和: {np.sum(np.abs(qstate.amplitudes)**2):.4f}")

    # 纠缠度量
    entanglement = QuantumCorrelationDetector.entanglement_measure(qstate)
    print(f"纠缠度量: {entanglement:.4f}")

    # 对比：经典IHT
    print("\n--- 与经典IHT对比 ---")
    from iht import iht

    A = np.random.randn(m, n) / np.sqrt(m)
    y = A @ x_true

    x_classical, _, _ = iht(A, y, s)
    err_classical = np.linalg.norm(x_classical - x_true) / np.linalg.norm(x_true)
    print(f"经典IHT误差: {err_classical:.6f}")
    print(f"量子IST误差: {error:.6f}")


if __name__ == "__main__":
    test_quantum_cs()
