# -*- coding: utf-8 -*-
"""
算法实现：量子机器学习 / quantum_k_means

本文件实现 quantum_k_means 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Cluster:
    """聚类簇"""
    center: np.ndarray
    points: List[np.ndarray]
    id: int


class Quantum_Distance_Calculator:
    """量子距离计算器"""
    def __init__(self, num_qubits: int = 8):
        self.num_qubits = num_qubits
        self.dimension_limit = 2 ** num_qubits


    def encode_vector(self, x: np.ndarray) -> np.ndarray:
        """将向量编码到量子态（振幅编码）"""
        # |x> = Σ x_i |i> / ||x||
        dim = len(x)
        if dim > self.dimension_limit:
            # 截断
            dim = self.dimension_limit
            x = x[:dim]
        state = np.zeros(self.dimension_limit, dtype=complex)
        norm = np.linalg.norm(x)
        if norm > 1e-10:
            state[:dim] = x / norm
        else:
            state[0] = 1.0
        return state


    def compute_distance(self, x: np.ndarray, y: np.ndarray) -> float:
        """
        计算两个向量的欧氏距离的平方
        d²(x,y) = ||x-y||² = ||x||² + ||y||² - 2<x|y>
        使用量子内积估计
        """
        state_x = self.encode_vector(x)
        state_y = self.encode_vector(y)
        # 计算内积 <x|y>
        inner_product = np.vdot(state_x, state_y)
        # 归一化
        norm_x = np.linalg.norm(x)
        norm_y = np.linalg.norm(y)
        if norm_x < 1e-10 or norm_y < 1e-10:
            return 0.0
        # 内积的估计值
        fidelity = np.abs(inner_product) ** 2
        # cos²(θ) = |<x|y>|² / (||x||² ||y||²)
        cos_sq = fidelity / (norm_x ** 2 * norm_y ** 2) if norm_x > 0 and norm_y > 0 else 0
        # 距离平方
        dist_sq = norm_x ** 2 + norm_y ** 2 - 2 * norm_x * norm_y * np.sqrt(cos_sq)
        return max(0, dist_sq)


    def compute_distances_to_centers(self, point: np.ndarray, centers: List[np.ndarray]) -> np.ndarray:
        """计算点到所有中心的距离"""
        distances = np.zeros(len(centers))
        for i, center in enumerate(centers):
            distances[i] = self.compute_distance(point, center)
        return distances


class Quantum_K_Means:
    """量子K-means聚类"""
    def __init__(self, k: int, max_iterations: int = 100, tolerance: float = 1e-4):
        self.k = k
        self.max_iterations = max_iterations
        self.tolerance = tolerance
        self.distance_calculator = Quantum_Distance_Calculator()
        self.centers: List[np.ndarray] = []
        self.clusters: List[Cluster] = []
        self.iteration_history: List[dict] = []


    def _initialize_centers(self, X: np.ndarray):
        """K-means++初始化"""
        n = len(X)
        # 选择第一个中心
        self.centers = [X[np.random.randint(0, n)]]
        # 选择剩余k-1个中心
        for _ in range(self.k - 1):
            # 计算每个点到最近中心的距离平方
            distances = np.zeros(n)
            for i, point in enumerate(X):
                min_dist = min(self.distance_calculator.compute_distance(point, c) for c in self.centers)
                distances[i] = min_dist
            # 概率选择下一个中心
            probs = distances / distances.sum()
            next_center_idx = np.random.choice(n, p=probs)
            self.centers.append(X[next_center_idx])


    def _assign_clusters(self, X: np.ndarray) -> List[int]:
        """将每个点分配到最近的聚类中心"""
        assignments = []
        for point in X:
            distances = self.distance_calculator.compute_distances_to_centers(point, self.centers)
            cluster_id = np.argmin(distances)
            assignments.append(cluster_id)
        return assignments


    def _update_centers(self, X: np.ndarray, assignments: List[int]):
        """更新聚类中心"""
        new_centers = []
        for i in range(self.k):
            cluster_points = [X[j] for j in range(len(X)) if assignments[j] == i]
            if cluster_points:
                # 计算质心
                new_center = np.mean(cluster_points, axis=0)
                new_centers.append(new_center)
            else:
                # 空聚类：保持原样或重新随机选择
                new_centers.append(self.centers[i])
        # 检查收敛
        max_shift = max(np.linalg.norm(new_centers[i] - self.centers[i]) for i in range(self.k))
        self.centers = new_centers
        return max_shift


    def fit(self, X: np.ndarray, verbose: bool = True):
        """拟合模型"""
        n = len(X)
        dim = X.shape[1] if len(X) > 0 else 0
        if verbose:
            print(f"量子K-means: k={self.k}, n={n}, dim={dim}")
        # 初始化
        self._initialize_centers(X)
        if verbose:
            print(f"  初始中心已选择")
        # 迭代
        for iteration in range(self.max_iterations):
            # 分配聚类
            assignments = self._assign_clusters(X)
            # 更新中心
            max_shift = self._update_centers(X, assignments)
            # 记录历史
            inertia = self._compute_inertia(X, assignments)
            self.iteration_history.append({
                'iteration': iteration,
                'inertia': inertia,
                'max_shift': max_shift
            })
            if verbose and iteration % 5 == 0:
                print(f"  Iteration {iteration}: inertia={inertia:.4f}, max_shift={max_shift:.6f}")
            # 检查收敛
            if max_shift < self.tolerance:
                if verbose:
                    print(f"  收敛于迭代 {iteration}")
                break
        # 创建聚类对象
        self.clusters = []
        for i in range(self.k):
            cluster_points = [X[j] for j in range(len(X)) if assignments[j] == i]
            self.clusters.append(Cluster(center=self.centers[i], points=cluster_points, id=i))


    def _compute_inertia(self, X: np.ndarray, assignments: List[int]) -> float:
        """计算惯性（聚类内平方和）"""
        inertia = 0.0
        for i, point in enumerate(X):
            cluster_id = assignments[i]
            dist = self.distance_calculator.compute_distance(point, self.centers[cluster_id])
            inertia += dist
        return inertia


    def predict(self, X: np.ndarray) -> List[int]:
        """预测聚类标签"""
        return self._assign_clusters(X)


def generate_clustering_data(n_samples: int = 100, k: int = 3, seed: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """生成分类数据"""
    np.random.seed(seed)
    X = []
    y = []
    centers = [
        np.array([0, 0]),
        np.array([5, 5]),
        np.array([10, 0]),
    ]
    for i in range(n_samples):
        cluster_id = i % k
        point = centers[cluster_id] + np.random.randn(2) * 0.5
        X.append(point)
        y.append(cluster_id)
    return np.array(X), np.array(y)


def basic_test():
    """基本功能测试"""
    print("=== 量子K-means聚类测试 ===")
    # 生成数据
    X, y_true = generate_clustering_data(n_samples=60, k=3)
    print(f"数据: {len(X)} 样本, 特征维度: {X[0].shape}")
    # 量子K-means
    print("\n运行量子K-means...")
    qkmeans = Quantum_K_Means(k=3, max_iterations=50, tolerance=1e-4)
    qkmeans.fit(X, verbose=True)
    # 预测
    predictions = qkmeans.predict(X)
    # 评估
    accuracy = np.mean(predictions == y_true)
    print(f"\n聚类准确率: {accuracy:.2%}")
    # 对比经典K-means
    print("\n对比经典K-means...")
    from sklearn.cluster import KMeans
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    kmeans.fit(X)
    classical_pred = kmeans.predict(X)
    # 计算调整兰德指数
    from sklearn.metrics import adjusted_rand_score
    ari = adjusted_rand_score(y_true, classical_pred)
    print(f"  经典K-means 调整兰德指数: {ari:.4f}")
    # 打印聚类统计
    print(f"\n聚类统计:")
    for i, cluster in enumerate(qkmeans.clusters):
        print(f"  聚类{i}: {len(cluster.points)} 点, 中心={cluster.center}")


if __name__ == "__main__":
    basic_test()
