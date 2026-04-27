# -*- coding: utf-8 -*-
"""
算法实现：量子机器学习 / qaoa_enhanced

本文件实现 qaoa_enhanced 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Optional, Callable
from dataclasses import dataclass
import random


@dataclass
class QAOA_Config:
    """QAOA配置"""
    num_qubits: int
    depth: int = 2  # p层
    gamma_range: Tuple[float, float] = (0, 2 * np.pi)
    beta_range: Tuple[float, float] = (0, np.pi)


class Cost_Hamiltonian:
    """Cost Hamiltonian（问题相关的Hamiltonian）"""
    def __init__(self, num_qubits: int):
        self.num_qubits = num_qubits
        self.terms: List[Tuple[float, List[int]]] = []  # (系数, qubit_indices)


    def add_term(self, coeff: float, qubits: List[int]):
        """添加Cost项"""
        self.terms.append((coeff, qubits))


    def add_quadratic_term(self, coeff: float, qubit1: int, qubit2: int):
        """添加二次项（双量子比特相互作用）"""
        self.terms.append((coeff, [qubit1, qubit2]))


    def add_linear_term(self, coeff: float, qubit: int):
        """添加线性项（单量子比特）"""
        self.terms.append((coeff, [qubit]))


    def evaluate(self, state: np.ndarray) -> float:
        """评估给定二值状态的Cost值"""
        cost = 0.0
        for coeff, qubits in self.terms:
            if len(qubits) == 1:
                # Z项：cost += coeff * σ_z
                cost += coeff * state[qubits[0]]
            elif len(qubits) == 2:
                # ZZ项：cost += coeff * σ_z ⊗ σ_z
                cost += coeff * state[qubits[0]] * state[qubits[1]]
        return cost


class Mixer_Hamiltonian:
    """Mixer Hamiltonian（混合器）"""
    def __init__(self, num_qubits: int, mixer_type: str = "x"):
        self.num_qubits = num_qubits
        self.mixer_type = mixer_type


    def apply(self, state: np.ndarray, beta: float) -> np.ndarray:
        """应用Mixer（exp(-i β B)）"""
        new_state = state.copy()
        if self.mixer_type == "x":
            # X mixer: 翻转比特
            for i in range(self.num_qubits):
                new_state[i] = state[i] * np.cos(beta) + (1 - state[i]) * np.sin(beta) if random.random() > 0.5 else state[i]
        return new_state


class QAOA:
    """QAOA算法"""
    def __init__(self, cost_hamiltonian: Cost_Hamiltonian, config: QAOA_Config):
        self.C = cost_hamiltonian
        self.config = config
        self.mixer = Mixer_Hamiltonian(config.num_qubits)
        self.parameters: np.ndarray = np.random.uniform(0, 1, 2 * config.depth)
        self.best_energy: float = float('inf')
        self.energy_history: List[float] = []


    def _prepare_state(self, gamma: float) -> np.ndarray:
        """制备叠加态（简化）"""
        # 实际需要从|0...0>开始，应用问题哈密顿量的演化
        # 简化为均匀叠加
        state = np.ones(2 ** self.config.num_qubits) / np.sqrt(2 ** self.config.num_qubits)
        return state


    def compute_expectation(self, parameters: np.ndarray) -> float:
        """计算给定参数的期望能量"""
        gamma_params = parameters[:self.config.depth]
        beta_params = parameters[self.config.depth:]
        # 简化的期望值计算
        # 实际需要模拟量子电路
        energy = 0.0
        for i, (coeff, qubits) in enumerate(self.C.terms):
            # 简化：使用随机估计
            energy += coeff * np.random.uniform(-1, 1)
        return energy


    def optimize(self, max_iterations: int = 100, learning_rate: float = 0.1, verbose: bool = True) -> Tuple[np.ndarray, float]:
        """优化QAOA参数"""
        params = self.parameters.copy()
        for iteration in range(max_iterations):
            # 计算梯度（数值）
            gradients = np.zeros_like(params)
            epsilon = 1e-3
            for i in range(len(params)):
                params_plus = params.copy()
                params_plus[i] += epsilon
                params_minus = params.copy()
                params_minus[i] -= epsilon
                gradients[i] = (self.compute_expectation(params_plus) - self.compute_expectation(params_minus)) / (2 * epsilon)
            # 梯度下降
            params -= learning_rate * gradients
            # 限制在有效范围内
            params[:self.config.depth] = np.clip(params[:self.config.depth], *self.config.gamma_range)
            params[self.config.depth:] = np.clip(params[self.config.depth:], *self.config.beta_range)
            # 记录能量
            energy = self.compute_expectation(params)
            self.energy_history.append(energy)
            if energy < self.best_energy:
                self.best_energy = energy
            if verbose and iteration % 20 == 0:
                print(f"  Iter {iteration}: E = {energy:.4f}")
        self.parameters = params
        return params, self.best_energy


    def sample_solution(self, num_samples: int = 100) -> List[Tuple[np.ndarray, float]]:
        """采样多个解"""
        solutions = []
        for _ in range(num_samples):
            # 简化的采样
            state = np.random.choice([1, -1], size=self.config.num_qubits)
            energy = self.C.evaluate(state)
            solutions.append((state, energy))
        # 按能量排序
        solutions.sort(key=lambda x: x[1])
        return solutions


class MaxCut_QAOA(QAOA):
    """MaxCut问题的QAOA"""
    def __init__(self, num_vertices: int, edges: List[Tuple[int, int]], depth: int = 2):
        # 构建MaxCut Cost Hamiltonian
        # MaxCut: 最大化切割边 = Σ (1 - σ_i σ_j)/2
        # C = Σ w_ij (1 - σ_i σ_j)/2
        cost = Cost_Hamiltonian(num_vertices)
        for i, j in edges:
            cost.add_quadratic_term(-0.5, i, j)  # MaxCut使用-1/2系数
            cost.add_linear_term(0.5 * len(edges), i)  # 常数项
        config = QAOA_Config(num_qubits=num_vertices, depth=depth)
        super().__init__(cost, config)
        self.edges = edges


    def compute_maxcut_value(self, state: np.ndarray) -> int:
        """计算MaxCut切割值"""
        cut = 0
        for i, j in self.edges:
            if state[i] != state[j]:
                cut += 1
        return cut


def basic_test():
    """基本功能测试"""
    print("=== 增强QAOA测试 ===")
    # MaxCut问题
    print("\n[MaxCut问题]")
    num_vertices = 6
    edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0), (0, 3), (1, 4)]
    print(f"顶点数: {num_vertices}, 边数: {len(edges)}")
    # 创建QAOA
    qaoa = MaxCut_QAOA(num_vertices, edges, depth=3)
    print(f"QAOA深度: {qaoa.config.depth}")
    # 优化
    print("\n优化QAOA参数...")
    optimal_params, best_energy = qaoa.optimize(max_iterations=50, verbose=True)
    # 采样解
    print("\n采样解:")
    solutions = qaoa.sample_solution(num_samples=20)
    for i, (state, energy) in enumerate(solutions[:5]):
        cut_value = qaoa.compute_maxcut_value(state)
        print(f"  解{i+1}: 切割值={cut_value}, 能量={energy:.4f}, 态={state}")
    # 经典对比（贪婪）
    print("\n经典贪婪算法对比:")
    best_greedy = 0
    for _ in range(100):
        state = np.random.choice([1, -1], size=num_vertices)
        cut = qaoa.compute_maxcut_value(state)
        if cut > best_greedy:
            best_greedy = cut
    print(f"  贪婪最佳切割: {best_greedy}")
    # 与QAOA对比
    if solutions:
        qaoa_best_cut = qaoa.compute_maxcut_value(solutions[0][0])
        print(f"  QAOA最佳切割: {qaoa_best_cut}")


if __name__ == "__main__":
    basic_test()
