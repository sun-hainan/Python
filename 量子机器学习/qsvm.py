# -*- coding: utf-8 -*-
"""
算法实现：量子机器学习 / qsvm

本文件实现 qsvm 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class Kernel_Type(Enum):
    """核函数类型"""
    QUANTUM_FIDELITY = "fidelity"       # 保真度核
    QUANTUM_PROJECTIVE = "projective"    # 投影核
    QUANTUM_ANGLE = "angle"             # 角度核


@dataclass
class Quantum_Feature_Map:
    """量子特征映射 φ(x)"""
    num_qubits: int
    depth: int
    parameters: np.ndarray


    def map(self, x: np.ndarray) -> np.ndarray:
        """
        将经典数据x映射到量子态 |φ(x)>
        返回态向量
        """
        # 简化：使用振幅编码
        # |φ(x)> = Σ x_i |i> / ||x||
        norm = np.linalg.norm(x)
        if norm < 1e-10:
            state = np.zeros(2 ** self.num_qubits, dtype=complex)
            state[0] = 1.0
        else:
            # 使用数据的振幅编码
            dim = min(len(x), 2 ** self.num_qubits)
            state = np.zeros(2 ** self.num_qubits, dtype=complex)
            state[:dim] = x[:dim] / norm
        return state


class Quantum_Kernel:
    """量子核函数"""
    def __init__(self, feature_map: Quantum_Feature_Map, kernel_type: Kernel_Type = Kernel_Type.QUANTUM_FIDELITY):
        self.feature_map = feature_map
        self.kernel_type = kernel_type


    def compute(self, x: np.ndarray, y: np.ndarray) -> float:
        """
        计算量子核 K(x, y) = |<φ(x)|φ(y)>|^2 或 <φ(x)|φ(y)>
        """
        state_x = self.feature_map.map(x)
        state_y = self.feature_map.map(y)
        if self.kernel_type == Kernel_Type.QUANTUM_FIDELITY:
            # 保真度核 K(x,y) = |<φ(x)|φ(y)>|^2
            inner_product = np.vdot(state_x, state_y)
            return np.abs(inner_product) ** 2
        elif self.kernel_type == Kernel_Type.QUANTUM_ANGLE:
            # 角度核 K(x,y) = <φ(x)|φ(y)>
            return np.vdot(state_x, state_y).real
        else:
            return np.abs(np.vdot(state_x, state_y)) ** 2


    def matrix(self, X: np.ndarray) -> np.ndarray:
        """计算整个核矩阵"""
        n = len(X)
        K = np.zeros((n, n))
        for i in range(n):
            for j in range(i, n):
                k = self.compute(X[i], X[j])
                K[i, j] = k
                K[j, i] = k
        return K


class Quantum_SVM:
    """量子支持向量机（使用量子核的SVM）"""
    def __init__(self, kernel: Quantum_Kernel, C: float = 1.0):
        self.kernel = kernel
        self.C = C  # 正则化参数
        self.support_vectors: Optional[np.ndarray] = None
        self.alphas: Optional[np.ndarray] = None
        self.b: float = 0.0
        self.kernel_matrix: Optional[np.ndarray] = None


    def fit(self, X: np.ndarray, y: np.ndarray, verbose: bool = True):
        """训练QSVM"""
        n = len(X)
        # 计算核矩阵
        if verbose:
            print(f"计算 {n}x{n} 核矩阵...")
        K = self.kernel.matrix(X)
        self.kernel_matrix = K
        # 使用二次规划求解对偶问题
        # min_α Σ α_i - 1/2 Σ α_i α_j y_i y_j K(x_i, x_j)
        # s.t. 0 ≤ α_i ≤ C, Σ α_i y_i = 0
        # 简化：使用随机梯度下降近似
        alphas = np.zeros(n)
        b = 0.0
        learning_rate = 0.01
        for epoch in range(100):
            for i in range(n):
                # 计算预测
                pred = sum(alphas[j] * y[j] * K[j, i] for j in range(n)) + b
                # 更新alpha
                if y[i] * pred < 1:
                    alphas[i] += learning_rate * (1 - y[i] * pred)
                    alphas[i] = max(0, min(self.C, alphas[i]))
            # 更新b
            b = sum(y[i] - sum(alphas[j] * y[j] * K[j, i] for j in range(n)) for i in range(n)) / max(1, sum(alphas > 0))))
        self.alphas = alphas
        self.b = b
        # 记录支持向量
        sv_indices = alphas > 1e-5
        self.support_vectors = X[sv_indices]
        if verbose:
            print(f"训练完成: {sum(sv_indices)} 个支持向量")


    def predict(self, x: np.ndarray) -> np.ndarray:
        """预测"""
        if self.support_vectors is None:
            raise ValueError("模型未训练")
        n_sv = len(self.support_vectors)
        predictions = []
        for sample in x:
            # 计算核函数值
            k_values = np.array([self.kernel.compute(sample, sv) for sv in self.support_vectors])
            # 分类决策
            decision = np.sum(self.alphas[self.alphas > 1e-5][:n_sv] * k_values) + self.b
            predictions.append(1 if decision >= 0 else -1)
        return np.array(predictions)


def generate_classification_data(n_samples: int = 50, noise: float = 0.1) -> Tuple[np.ndarray, np.ndarray]:
    """生成分类数据"""
    np.random.seed(42)
    # 两个类别的数据
    n_half = n_samples // 2
    # 类别1：中心在(0, 0)
    X1 = np.random.randn(n_half, 2) * noise + np.array([0, 0])
    # 类别2：中心在(1, 1)
    X2 = np.random.randn(n_half, 2) * noise + np.array([1, 1])
    X = np.vstack([X1, X2])
    y = np.array([1] * n_half + [-1] * n_half)
    return X, y


def basic_test():
    """基本功能测试"""
    print("=== 量子支持向量机测试 ===")
    # 生成数据
    X, y = generate_classification_data(n_samples=40)
    print(f"数据: {len(X)} 样本, 特征维度: {X.shape[1]}")
    # 创建量子特征映射
    feature_map = Quantum_Feature_Map(num_qubits=3, depth=2, parameters=np.random.rand(10))
    # 创建量子核
    kernel = Quantum_Kernel(feature_map, kernel_type=Kernel_Type.QUANTUM_FIDELITY)
    # 测试核函数
    print(f"\n测试量子核函数:")
    print(f"  K(x1, x2) = {kernel.compute(X[0], X[1]):.4f}")
    print(f"  K(x1, x1) = {kernel.compute(X[0], X[0]):.4f}")
    # 训练QSVM
    print("\n训练QSVM...")
    qsvm = Quantum_SVM(kernel, C=1.0)
    qsvm.fit(X, y)
    # 预测
    predictions = qsvm.predict(X)
    accuracy = np.mean(predictions == y)
    print(f"\n训练准确率: {accuracy:.2%}")
    print(f"支持向量数: {len(qsvm.support_vectors)}")
    # 与经典SVM对比
    print("\n与经典RBF核SVM对比:")
    from sklearn.svm import SVC
    classical_svm = SVC(kernel='rbf', C=1.0)
    classical_svm.fit(X, y)
    classical_pred = classical_svm.predict(X)
    classical_acc = np.mean(classical_pred == y)
    print(f"  经典RBF SVM准确率: {classical_acc:.2%}")


if __name__ == "__main__":
    basic_test()
