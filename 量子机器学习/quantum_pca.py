# -*- coding: utf-8 -*-
"""
算法实现：量子机器学习 / quantum_pca

本文件实现 quantum_pca 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Data_Matrix:
    """数据矩阵"""
    data: np.ndarray
    num_samples: int
    num_features: int


class Quantum_RAM:
    """量子随机存取存储器（简化实现）"""
    def __init__(self, num_qubits: int):
        self.num_qubits = num_qubits
        self.capacity = 2 ** num_qubits
        self.memory: np.ndarray = np.zeros(self.capacity, dtype=complex)


    def load_vector(self, data: np.ndarray):
        """加载向量到QRAM（振幅编码）"""
        n = len(data)
        if n > self.capacity:
            # 截断
            n = self.capacity
            data = data[:n]
        norm = np.linalg.norm(data)
        if norm > 1e-10:
            self.memory[:n] = data / norm
        else:
            self.memory[0] = 1.0


    def load_matrix(self, matrix: np.ndarray):
        """加载矩阵到QRAM（按行）"""
        # 简化：只加载第一行
        if len(matrix) > 0:
            self.load_vector(matrix[0])


    def query(self, index: int) -> complex:
        """查询指定索引的值"""
        if 0 <= index < self.capacity:
            return self.memory[index]
        return 0


class Quantum_PCA:
    """量子主成分分析"""
    def __init__(self, num_qubits: int = 10):
        self.num_qubits = num_qubits
        self.qram = Quantum_RAM(num_qubits)
        self.eigenvalues: Optional[np.ndarray] = None
        self.eigenvectors: Optional[np.ndarray] = None
        self.cumulative_variance: Optional[np.ndarray] = None


    def _compute_covariance_matrix(self, data: np.ndarray) -> np.ndarray:
        """计算协方差矩阵（经典）"""
        # 中心化
        centered = data - np.mean(data, axis=0)
        # 协方差
        cov = (centered.T @ centered) / (len(data) - 1)
        return cov


    def _quantum_phase_estimation(self, matrix: np.ndarray, num_qubits: int = 10) -> np.ndarray:
        """
        量子相位估计（简化）
        实际需要使用量子电路来估计特征值
        """
        # 简化：使用经典特征值作为估计
        eigenvalues, _ = np.linalg.eigh(matrix)
        # 取绝对值并排序
        eigenvalues = np.sort(np.abs(eigenvalues))[::-1]
        return eigenvalues


    def fit(self, data: np.ndarray, n_components: int = 2, verbose: bool = True):
        """拟合PCA模型"""
        self.data_matrix = Data_Matrix(data=data, num_samples=len(data), num_features=data.shape[1])
        if verbose:
            print(f"QPCA: {self.data_matrix.num_samples} 样本, {self.data_matrix.num_features} 特征")
        # 计算协方差矩阵
        cov = self._compute_covariance_matrix(data)
        # 加载到QRAM
        self.qram.load_matrix(cov)
        # 量子相位估计获取特征值
        eigenvalues = self._quantum_phase_estimation(cov)
        # 归一化特征值（作为方差解释比例）
        total_variance = np.sum(eigenvalues)
        if total_variance > 1e-10:
            explained_variance_ratio = eigenvalues / total_variance
        else:
            explained_variance_ratio = np.ones_like(eigenvalues) / len(eigenvalues)
        self.eigenvalues = eigenvalues
        self.cumulative_variance = np.cumsum(explained_variance_ratio)
        # 计算特征向量（简化：使用随机投影）
        self.eigenvectors = np.random.randn(data.shape[1], n_components) * 0.1
        if verbose:
            print(f"  前3个主成分解释方差: {self.cumulative_variance[:3]}")
            print(f"  累计解释方差: {self.cumulative_variance[n_components-1]:.4f}")


    def transform(self, data: np.ndarray, n_components: int = None) -> np.ndarray:
        """变换数据到主成分空间"""
        if n_components is None:
            n_components = self.eigenvectors.shape[1]
        # 投影到主成分
        centered = data - np.mean(data, axis=0)
        transformed = centered @ self.eigenvectors[:, :n_components]
        return transformed


    def fit_transform(self, data: np.ndarray, n_components: int = 2) -> np.ndarray:
        """拟合并变换"""
        self.fit(data, n_components)
        return self.transform(data, n_components)


    def inverse_transform(self, components: np.ndarray) -> np.ndarray:
        """逆变换回原始空间"""
        reconstructed = components @ self.eigenvectors.T
        return reconstructed + np.mean(self.data_matrix.data, axis=0)


def generate_pca_data(n_samples: int = 100, noise: float = 0.1) -> np.ndarray:
    """生成适合PCA的数据（低秩+噪声）"""
    np.random.seed(42)
    # 潜在变量
    t = np.linspace(0, 2 * np.pi, n_samples)
    z1 = np.sin(t)
    z2 = np.cos(t)
    # 生成高维数据
    X = np.zeros((n_samples, 10))
    X[:, 0] = z1 + np.random.randn(n_samples) * noise
    X[:, 1] = z2 + np.random.randn(n_samples) * noise
    X[:, 2] = z1 * z2 + np.random.randn(n_samples) * noise
    X[:, 3:7] = np.random.randn(n_samples, 4) * 0.5
    X[:, 7:] = np.random.randn(n_samples, 3) * 2
    return X


def basic_test():
    """基本功能测试"""
    print("=== 量子主成分分析测试 ===")
    # 生成数据
    X = generate_pca_data(n_samples=100)
    print(f"数据形状: {X.shape}")
    # 量子PCA
    print("\n运行量子PCA...")
    qpca = Quantum_PCA(num_qubits=10)
    X_transformed = qpca.fit_transform(X, n_components=3)
    print(f"变换后形状: {X_transformed.shape}")
    print(f"特征值（前5个）: {qpca.eigenvalues[:5]}")
    print(f"累计解释方差: {qpca.cumulative_variance[:5]}")
    # 与经典PCA对比
    print("\n对比经典PCA...")
    from sklearn.decomposition import PCA
    classical_pca = PCA(n_components=3)
    X_classical = classical_pca.fit_transform(X)
    print(f"  经典PCA解释方差比: {classical_pca.explained_variance_ratio_}")
    # 重构误差对比
    X_qpca_rec = qpca.inverse_transform(X_transformed)
    X_classical_rec = classical_pca.inverse_transform(X_classical)
    qpca_error = np.mean((X - X_qpca_rec) ** 2)
    classical_error = np.mean((X - X_classical_rec) ** 2)
    print(f"\n重构误差:")
    print(f"  QPCA: {qpca_error:.6f}")
    print(f"  Classical PCA: {classical_error:.6f}")


if __name__ == "__main__":
    basic_test()
