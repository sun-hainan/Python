# -*- coding: utf-8 -*-
"""
算法实现：量子机器学习 / quantum_gradient

本文件实现 quantum_gradient 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Callable, Optional
from dataclasses import dataclass


@dataclass
class Optimization_Result:
    """优化结果"""
    optimal_parameters: np.ndarray
    optimal_value: float
    iterations: int
    history: List[float]


class Parameterized_Quantum_Circuit:
    """参数化量子电路（用于梯度计算）"""
    def __init__(self, num_qubits: int, num_layers: int):
        self.num_qubits = num_qubits
        self.num_layers = num_layers
        self.num_parameters = num_layers * num_qubits * 3


    def forward(self, parameters: np.ndarray, x: np.ndarray = None) -> float:
        """
        前向传播
        简化：返回参数的正弦函数组合
        """
        # 简化的能量函数
        energy = np.sum(np.sin(parameters)) + np.sum(parameters ** 2) / 100
        return energy


class Quantum_Gradient_Estimator:
    """量子梯度估计器"""
    def __init__(self, pqc: Parameterized_Quantum_Circuit):
        self.pqc = pqc


    def estimate_gradient(self, parameters: np.ndarray, epsilon: float = 0.01) -> np.ndarray:
        """
        使用参数偏移法估计梯度
        ∂E/∂θ_i ≈ (E(θ + εe_i) - E(θ - εe_i)) / 2ε
        """
        gradients = np.zeros_like(parameters)
        for i in range(len(parameters)):
            params_plus = parameters.copy()
            params_plus[i] += epsilon
            params_minus = parameters.copy()
            params_minus[i] -= epsilon
            gradients[i] = (self.pqc.forward(params_plus) - self.pqc.forward(params_minus)) / (2 * epsilon)
        return gradients


class Quantum_Natural_Gradient_Optimizer:
    """量子自然梯度优化器"""
    def __init__(self, pqc: Parameterized_Quantum_Circuit, learning_rate: float = 0.1):
        self.pqc = pqc
        self.lr = learning_rate
        self.gradient_estimator = Quantum_Gradient_Estimator(pqc)


    def _compute_fisher_information(self, parameters: np.ndarray, n_samples: int = 10) -> np.ndarray:
        """
        计算量子Fisher信息矩阵（简化）
        实际需要测量量子态的统计量
        """
        # 简化：使用单位矩阵（忽略参数依赖的Fisher信息）
        # 真实实现需要计算 |∂ψ/∂θ_i>
        dim = len(parameters)
        F = np.eye(dim) * 0.1
        return F


    def step(self, parameters: np.ndarray) -> np.ndarray:
        """执行一步自然梯度下降"""
        # 计算梯度
        gradient = self.gradient_estimator.estimate_gradient(parameters)
        # 计算Fisher信息矩阵
        F = self._compute_fisher_information(parameters)
        # 自然梯度：F^(-1) ∇E
        try:
            F_inv = np.linalg.inv(F + 1e-6 * np.eye(len(parameters)))
        except np.linalg.LinAlgError:
            F_inv = np.eye(len(parameters))
        natural_gradient = F_inv @ gradient
        # 更新参数
        new_params = parameters - self.lr * natural_gradient
        return new_params


class Quantum_Gradient_Descent:
    """量子梯度下降优化器"""
    def __init__(self, pqc: Parameterized_Quantum_Circuit, method: str = "steepest", learning_rate: float = 0.1):
        self.pqc = pqc
        self.method = method
        self.lr = learning_rate
        self.gradient_estimator = Quantum_Gradient_Estimator(pqc)
        if method == "natural":
            self.optimizer = Quantum_Natural_Gradient_Optimizer(pqc, learning_rate)


    def optimize(self, initial_params: np.ndarray, max_iterations: int = 100,
                tolerance: float = 1e-6, verbose: bool = True) -> Optimization_Result:
        """执行优化"""
        params = initial_params.copy()
        history = []
        for iteration in range(max_iterations):
            # 计算能量
            current_value = self.pqc.forward(params)
            history.append(current_value)
            if verbose and iteration % 10 == 0:
                print(f"  Iter {iteration}: E = {current_value:.6f}")
            # 计算梯度
            gradient = self.gradient_estimator.estimate_gradient(params)
            # 检查收敛
            if np.linalg.norm(gradient) < tolerance:
                if verbose:
                    print(f"  收敛于迭代 {iteration}")
                break
            # 更新参数
            if self.method == "steepest":
                params = params - self.lr * gradient
            elif self.method == "natural":
                params = self.optimizer.step(params)
            else:
                params = params - self.lr * gradient
        return Optimization_Result(
            optimal_parameters=params,
            optimal_value=history[-1] if history else float('inf'),
            iterations=iteration + 1,
            history=history
        )


class Adam_Quantum_Optimizer:
    """Adam量子优化器"""
    def __init__(self, pqc: Parameterized_Quantum_Circuit, lr: float = 0.01,
                 beta1: float = 0.9, beta2: float = 0.999, epsilon: float = 1e-8):
        self.pqc = pqc
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.epsilon = epsilon
        self.gradient_estimator = Quantum_Gradient_Estimator(pqc)
        self.m: Optional[np.ndarray] = None
        self.v: Optional[np.ndarray] = None
        self.t: int = 0


    def step(self, params: np.ndarray) -> np.ndarray:
        """执行一步Adam优化"""
        self.t += 1
        gradient = self.gradient_estimator.estimate_gradient(params)
        # 初始化
        if self.m is None:
            self.m = np.zeros_like(params)
            self.v = np.zeros_like(params)
        # 更新一阶矩估计
        self.m = self.beta1 * self.m + (1 - self.beta1) * gradient
        # 更新二阶矩估计
        self.v = self.beta2 * self.v + (1 - self.beta2) * (gradient ** 2)
        # 偏差校正
        m_hat = self.m / (1 - self.beta1 ** self.t)
        v_hat = self.v / (1 - self.beta2 ** self.t)
        # 更新参数
        new_params = params - self.lr * m_hat / (np.sqrt(v_hat) + self.epsilon)
        return new_params


def basic_test():
    """基本功能测试"""
    print("=== 量子梯度下降测试 ===")
    # 创建PQC
    pqc = Parameterized_Quantum_Circuit(num_qubits=3, num_layers=2)
    print(f"PQC参数数: {pqc.num_parameters}")
    # 测试梯度估计
    print("\n测试梯度估计:")
    initial_params = np.random.uniform(0, 2 * np.pi, pqc.num_parameters)
    grad_est = Quantum_Gradient_Estimator(pqc)
    gradient = grad_est.estimate_gradient(initial_params)
    print(f"  梯度范数: {np.linalg.norm(gradient):.6f}")
    # 梯度下降
    print("\n梯度下降优化:")
    qgd = Quantum_Gradient_Descent(pqc, method="steepest", learning_rate=0.1)
    result = qgd.optimize(initial_params, max_iterations=50, verbose=True)
    print(f"  最优值: {result.optimal_value:.6f}")
    # 自然梯度下降
    print("\n自然梯度下降优化:")
    qngd = Quantum_Gradient_Descent(pqc, method="natural", learning_rate=0.1)
    result_ng = qngd.optimize(initial_params, max_iterations=50, verbose=True)
    print(f"  最优值: {result_ng.optimal_value:.6f}")
    # Adam
    print("\nAdam优化:")
    adam = Adam_Quantum_Optimizer(pqc, lr=0.1)
    for i in range(50):
        initial_params = adam.step(initial_params)
        if i % 10 == 0:
            print(f"  Iter {i}: E = {pqc.forward(initial_params):.6f}")


if __name__ == "__main__":
    basic_test()
