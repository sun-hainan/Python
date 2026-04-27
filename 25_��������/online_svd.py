# -*- coding: utf-8 -*-
"""
算法实现：25_�������� / online_svd

本文件实现 online_svd 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Optional
import math


class OnlineSVD:
    """
    在线SVD
    
    使用增量更新追踪数据流的主成分
    """
    
    def __init__(self, n_components: int = 2, n_features: int = None):
        """
        初始化
        
        Args:
            n_components: 要追踪的主成分数
            n_features: 特征维度
        """
        self.n_components = n_components
        self.n_features = n_features
        
        # 主成分矩阵
        self.components = None  # shape: (n_components, n_features)
        
        # 累积统计
        self.count = 0
        self.mean = None
        self.M = None  # 协方差矩阵的累积
        self.n_samples_seen = 0
    
    def partial_fit(self, X: np.ndarray):
        """
        在线增量学习
        
        Args:
            X: 新数据点 shape: (batch_size, n_features) 或 (n_features,)
        """
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        batch_size, n_features = X.shape
        
        if self.n_features is None:
            self.n_features = n_features
            self.mean = np.zeros(n_features)
            self.M = np.zeros((n_features, n_features))
        
        # 更新均值
        old_mean = self.mean.copy()
        self.mean += np.sum(X - old_mean, axis=0) / (self.n_samples_seen + batch_size)
        
        # 更新协方差矩阵
        # M = Σ (x - μ)(x - μ)^T
        for x in X:
            x_centered = x - self.mean
            self.M += np.outer(x_centered, x_centered)
        
        self.n_samples_seen += batch_size
        
        # 更新主成分
        self._update_components()
    
    def _update_components(self):
        """更新主成分"""
        if self.n_samples_seen < self.n_components:
            return
        
        # 使用幂迭代近似SVD
        self.components = self._power_iteration()
    
    def _power_iteration(self, n_iter: int = 5) -> np.ndarray:
        """
        幂迭代求主成分
        
        Args:
            n_iter: 迭代次数
        
        Returns:
            主成分矩阵
        """
        n = self.n_features
        
        # 初始化随机矩阵
        Q = np.random.randn(n, self.n_components)
        Q, _ = np.linalg.qr(Q)
        
        for _ in range(n_iter):
            # A = M
            # Q = A @ Q
            Z = self.M @ Q
            
            # 正交化
            Q, R = np.linalg.qr(Z)
        
        return Q.T  # shape: (n_components, n_features)
    
    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        将数据投影到主成分空间
        
        Args:
            X: 数据 shape: (n_samples, n_features)
        
        Returns:
            投影后的数据 shape: (n_samples, n_components)
        """
        if self.components is None:
            return np.zeros((X.shape[0], self.n_components))
        
        # 去中心化
        X_centered = X - self.mean
        
        # 投影
        return X_centered @ self.components.T
    
    def fit(self, X: np.ndarray):
        """批量学习（用于初始化）"""
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        self.n_features = X.shape[1]
        self.mean = np.mean(X, axis=0)
        self.n_samples_seen = X.shape[0]
        
        # 中心化
        X_centered = X - self.mean
        
        # 协方差矩阵
        self.M = X_centered.T @ X_centered
        
        # SVD
        _, _, Vt = np.linalg.svd(self.M)
        self.components = Vt[:self.n_components]
        
        return self


class IncrementalPCA:
    """
    增量PCA
    
    使用随机投影的增量PCA
    """
    
    def __init__(self, n_components: int = 2, batch_size: int = 100):
        self.n_components = n_components
        self.batch_size = batch_size
        
        self.W = None  # 投影矩阵
        self.count = 0
    
    def partial_fit(self, X: np.ndarray):
        """增量学习"""
        if self.W is None:
            self.W = np.random.randn(X.shape[1], self.n_components) * 0.1
            self.W, _ = np.linalg.qr(self.W)
        
        # 更新W
        residual = X - X @ self.W @ self.W.T
        self.W += residual @ self.W * 0.01  # 简化更新
        
        # 正交化
        self.W, _ = np.linalg.qr(self.W)
        
        self.count += X.shape[0]


class RandomSVD:
    """
    随机SVD
    
    使用随机投影高效计算近似SVD
    """
    
    def __init__(self, n_components: int = 2, n_oversamples: int = 5):
        self.n_components = n_components
        self.n_oversamples = n_oversamples
    
    def fit(self, A: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        随机SVD
        
        Args:
            A: 输入矩阵 shape: (m, n)
        
        Returns:
            (U, S, Vt) - 近似SVD分解
        """
        m, n = A.shape
        
        # 步骤1: 生成随机测试矩阵
        P = np.random.randn(n, self.n_components + self.n_oversamples)
        
        # 步骤2: 计算 Y = A @ P
        Y = A @ P
        
        # 步骤3: QR分解
        Q, _ = np.linalg.qr(Y)
        
        # 步骤4: B = Q.T @ A
        B = Q.T @ A
        
        # 步骤5: SVD on B
        Ub, Sb, Vtb = np.linalg.svd(B, full_matrices=False)
        
        # 步骤6: U = Q @ Ub
        U = Q @ Ub
        
        return U[:, :self.n_components], Sb[:self.n_components], Vtb[:self.n_components]


def demo_online_svd():
    """演示在线SVD"""
    print("=== 在线SVD演示 ===\n")
    
    np.random.seed(42)
    
    # 生成低秩数据
    print("生成低秩数据 (3个主方向):")
    
    # 真实主成分
    true_components = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 0.1],
    ])
    
    # 生成数据
    n_samples = 1000
    X = np.random.randn(n_samples, 3) @ true_components.T
    X += np.random.randn(n_samples, 3) * 0.1  # 添加噪声
    
    print(f"  数据形状: {X.shape}")
    print(f"  真实奇异值比例: {np.sqrt([3, 1, 0.01])}")
    
    # 批量SVD
    print("\n批量SVD结果:")
    U, S, Vt = np.linalg.svd(X, full_matrices=False)
    print(f"  奇异值: {S}")
    
    # 在线SVD
    print("\n在线SVD (流式学习):")
    online_svd = OnlineSVD(n_components=3, n_features=3)
    
    # 模拟流式输入
    batch_size = 50
    for i in range(0, n_samples, batch_size):
        batch = X[i:i+batch_size]
        online_svd.partial_fit(batch)
    
    print(f"  学习到的成分形状: {online_svd.components.shape}")
    print(f"  成分矩阵:\n{online_svd.components}")
    
    # 投影
    projected = online_svd.transform(X[:10])
    print(f"\n前10个样本的投影:\n{projected}")


def demo_random_projection():
    """演示随机投影"""
    print("\n=== 随机投影演示 ===\n")
    
    np.random.seed(42)
    
    # 高维数据
    n_samples = 500
    d_original = 100
    d_reduced = 10
    
    # 生成数据
    X = np.random.randn(n_samples, d_original)
    
    print(f"原始数据形状: {X.shape}")
    print(f"目标维度: {d_reduced}")
    
    # 随机SVD
    rsvd = RandomSVD(n_components=d_reduced)
    U, S, Vt = rsvd.fit(X)
    
    print(f"\n随机SVD结果:")
    print(f"  U shape: {U.shape}")
    print(f"  S: {S[:5]}... (前5个)")
    print(f"  Vt shape: {Vt.shape}")
    
    # 重构误差
    X_reconstructed = U @ np.diag(S) @ Vt
    error = np.linalg.norm(X - X_reconstructed) / np.linalg.norm(X)
    print(f"  重构相对误差: {error:.4f}")


def demo_streaming_pca():
    """演示流式PCA"""
    print("\n=== 流式PCA追踪 ===\n")
    
    np.random.seed(42)
    
    # 模拟分布变化
    print("模拟分布变化:")
    
    online_svd = OnlineSVD(n_components=2, n_features=2)
    
    # 阶段1: 高斯(0,0)
    print("  阶段1: 集中在原点")
    for _ in range(200):
        online_svd.partial_fit(np.random.randn(10, 2) * 0.5)
    
    # 阶段2: 高斯(5,5)
    print("  阶段2: 移动到(5,5)")
    for _ in range(200):
        online_svd.partial_fit(np.random.randn(10, 2) + 5)
    
    # 阶段3: 高斯(10,0)
    print("  阶段3: 移动到(10,0)")
    for _ in range(200):
        online_svd.partial_fit(np.random.randn(10, 2) + [10, 0])
    
    print(f"\n最终均值: {online_svd.mean}")
    print(f"主成分方向:\n{online_svd.components}")


def demo_reconstruction():
    """演示重构"""
    print("\n=== 在线重构演示 ===\n")
    
    np.random.seed(42)
    
    # 生成数据
    n = 100
    X = np.random.randn(n, 5)
    
    # 添加低秩结构
    true_low_rank = np.random.randn(n, 2) @ np.random.randn(2, 5)
    X = X + true_low_rank * 3
    
    print(f"数据形状: {X.shape}")
    
    # 在线学习
    online = OnlineSVD(n_components=2, n_features=5)
    
    for i in range(0, n, 10):
        online.partial_fit(X[i:i+10])
    
    # 重构
    projected = online.transform(X)
    reconstructed = projected @ online.components + online.mean
    
    error = np.linalg.norm(X - reconstructed) / np.linalg.norm(X)
    
    print(f"重构相对误差: {error:.4f}")
    print(f"原始数据方差解释比例: {1 - error**2:.4f}")


def demo_compression():
    """演示压缩"""
    print("\n=== 数据压缩演示 ===\n")
    
    # 原始数据存储
    n_samples = 10000
    n_features = 100
    n_components = 10
    
    original_storage = n_samples * n_features
    compressed_storage = n_samples * n_components + n_features + n_components
    
    print(f"原始存储: {original_storage:,} 浮点数")
    print(f"压缩后存储: {compressed_storage:,} 浮点数")
    print(f"压缩比: {original_storage/compressed_storage:.1f}x")
    
    print("\n压缩后包含:")
    print(f"  - 投影数据: {n_samples} × {n_components} = {n_samples * n_components:,}")
    print(f"  - 均值向量: {n_features}")
    print(f"  - 主成分: {n_components} × {n_features} = {n_components * n_features:,}")


if __name__ == "__main__":
    print("=" * 60)
    print("在线SVD 主成分追踪算法")
    print("=" * 60)
    
    # 在线SVD
    demo_online_svd()
    
    # 随机投影
    demo_random_projection()
    
    # 流式PCA
    demo_streaming_pca()
    
    # 重构
    demo_reconstruction()
    
    # 压缩
    demo_compression()
    
    print("\n" + "=" * 60)
    print("核心算法:")
    print("=" * 60)
    print("""
1. 增量协方差更新:
   M_new = M_old + Σ(x_i - μ_new)(x_i - μ_new)^T
   
2. 幂迭代:
   - 随机初始化Q
   - 迭代: Q = normalize(A @ Q)
   - 收敛到主成分
    
3. 随机投影SVD:
   - 用随机矩阵探测列空间
   - 基于小矩阵的SVD
   
4. 复杂度:
   - 空间: O(d^2) 存储协方差
   - 时间: O(d * n_components) 每批次
""")
