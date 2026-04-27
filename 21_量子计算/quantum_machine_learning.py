# -*- coding: utf-8 -*-
"""
算法实现：21_量子计算 / quantum_machine_learning

本文件实现 quantum_machine_learning 相关的算法功能。
"""

import numpy as np
from numpy.linalg import svd


class HHLAlgorithm:
    """
    HHL 算法（Harrow-Hassidim-Lloyd）
    
    用于求解线性方程组 Ax = b
    
    经典复杂度：O(N³) 对于稠密矩阵
    量子复杂度：O(log N * κ² * ε⁻¹)
    
    其中：
    - N: 矩阵维度
    - κ: 条件数
    - ε: 精度
    
    算法步骤：
    1. 态制备：|b⟩ = Σ b_i |i⟩
    2. 量子相位估计：特征值编码
    3. 条件旋转
    4. 逆 QPE
    5. 测量得到 |x⟩
    """
    
    def __init__(self, matrix_A, vector_b):
        """
        参数：
            matrix_A: n×n 厄米矩阵（需要正定）
            vector_b: n 维向量
        """
        self.A = np.array(matrix_A)
        self.b = np.array(vector_b)
        self.n = len(b)
    
    def validate_hermitian(self):
        """检查矩阵是否为厄米矩阵"""
        A = self.A
        is_hermitian = np.allclose(A, A.conj().T)
        return is_hermitian
    
    def compute_eigenvalues(self):
        """
        计算特征值（经典预处理）
        
        量子 HHL 中，特征值通过 QPE 获得
        """
        eigenvalues, eigenvectors = np.linalg.eigh(self.A)
        return eigenvalues, eigenvectors
    
    def hhl_solve(self, n_bits=3):
        """
        简化的 HHL 算法模拟
        
        参数：
            n_bits: QPE 的位数（决定精度）
        
        返回：解向量 x
        """
        eigenvalues, eigenvectors = self.compute_eigenvalues()
        
        # 检查条件数
        cond_num = max(abs(eigenvalues)) / min(abs(eigenvalues))
        print(f"  条件数 κ = {cond_num:.2f}")
        
        # 将 b 变换到特征基
        b_prime = eigenvectors.conj().T @ self.b
        b_prime = b_prime / np.linalg.norm(b_prime)  # 归一化
        
        # 模拟条件旋转和测量
        # 对于每个特征值 λ_i
        solution_amplitudes = []
        
        for i, lam in enumerate(eigenvalues):
            if abs(lam) < 1e-10:
                solution_amplitudes.append(0)
                continue
            
            # 计算旋转角度（基于 1/λ）
            C = abs(lam)  # 简化
            theta = np.arcsin(C / cond_num) if cond_num > 0 else 0
            
            # 振幅 = b'_i * sin(theta)
            amplitude = b_prime[i] * np.sin(theta)
            solution_amplitudes.append(amplitude)
        
        # 转换回原始基
        x_prime = np.array(solution_amplitudes)
        x = eigenvectors @ x_prime
        
        # 归一化
        norm_ratio = np.linalg.norm(self.b) / np.linalg.norm(x)
        x = x * norm_ratio
        
        return x
    
    def classical_solution(self):
        """经典求解（使用 NumPy）"""
        x = np.linalg.solve(self.A, self.b)
        return x
    
    def verify_solution(self, x):
        """验证解：Ax ≈ b"""
        residual = np.linalg.norm(self.A @ x - self.b)
        return residual


def quantum_distance(point1, point2, n_bits=8):
    """
    量子距离计算
    
    量子电路用于计算两点之间的距离：
    |ψ⟩ = (|point1⟩ + |point2⟩) / sqrt(2)
    
    使用 SWAP 测试估计内积
    内积 -> 距离 = sqrt(||a-b||²) = sqrt(||a||² + ||b||² - 2⟨a,b⟩)
    
    参数：
        point1, point2: 特征向量
        n_bits: 用于特征编码的量子比特数
    
    返回：欧氏距离的估计
    """
    # 归一化
    p1 = np.array(point1) / np.linalg.norm(point1)
    p2 = np.array(point2) / np.linalg.norm(point2)
    
    # 计算内积
    inner_product = np.abs(p1 @ p2.conj())
    
    # 模拟测量（带噪声）
    # 实际量子电路中，通过多次测量 SWAP 测试得到
    n_shots = 1000
    measured_ip = inner_product + np.random.normal(0, 0.1)
    measured_ip = np.clip(measured_ip, -1, 1)
    
    # 距离
    norm1_sq = np.sum(np.abs(point1) ** 2)
    norm2_sq = np.sum(np.abs(point2) ** 2)
    
    distance_sq = norm1_sq + norm2_sq - 2 * measured_ip * np.sqrt(norm1_sq * norm2_sq)
    distance = np.sqrt(max(0, distance_sq))
    
    return distance


class QKMeans:
    """
    量子 K-Means 聚类
    
    核心思想：
    - 距离计算使用量子电路（指数加速）
    - 聚类中心更新使用经典计算
    
    步骤：
    1. 准备数据量子态
    2. 使用量子距离计算
    3. 分配点到最近中心
    4. 更新中心
    """
    
    def __init__(self, n_clusters=3, n_iterations=10):
        self.k = n_clusters
        self.n_iterations = n_iterations
        self.centers = None
        self.labels = None
    
    def initialize_centers(self, data):
        """K-Means++ 初始化"""
        n = len(data)
        
        # 第一个中心随机选
        self.centers = [data[np.random.randint(n)]]
        
        # 选择剩余 k-1 个中心
        for _ in range(self.k - 1):
            # 计算每个点到最近中心的距离
            distances = []
            for point in data:
                min_dist = min(
                    np.linalg.norm(point - c) ** 2
                    for c in self.centers
                )
                distances.append(min_dist)
            
            # 按距离平方比例选择
            probs = np.array(distances) / sum(distances)
            new_center_idx = np.random.choice(n, p=probs)
            self.centers.append(data[new_center_idx])
    
    def quantum_assign_clusters(self, data):
        """
        使用量子距离计算分配聚类
        
        简化版：使用经典距离（真正的量子版本需要量子电路）
        """
        labels = []
        
        for point in data:
            distances = [
                quantum_distance(point, center)
                for center in self.centers
            ]
            nearest = np.argmin(distances)
            labels.append(nearest)
        
        return np.array(labels)
    
    def update_centers(self, data, labels):
        """更新聚类中心"""
        new_centers = []
        
        for cluster_id in range(self.k):
            cluster_points = data[labels == cluster_id]
            if len(cluster_points) > 0:
                new_center = np.mean(cluster_points, axis=0)
                new_centers.append(new_center)
            else:
                new_centers.append(self.centers[cluster_id])
        
        self.centers = new_centers
    
    def fit(self, data):
        """K-Means 拟合"""
        self.initialize_centers(data)
        
        for iteration in range(self.n_iterations):
            # 分配
            labels = self.quantum_assign_clusters(data)
            
            # 更新
            self.update_centers(data, labels)
            
            # 打印进度
            inertia = sum(
                np.linalg.norm(data[i] - self.centers[labels[i]]) ** 2
                for i in range(len(data))
            )
            print(f"  迭代 {iteration+1}: 惯性 = {inertia:.2f}")
        
        self.labels = labels
        return labels


if __name__ == "__main__":
    print("=" * 55)
    print("量子机器学习（Quantum Machine Learning）")
    print("=" * 55)
    
    # HHL 示例
    print("\n1. HHL 算法（线性方程组求解）")
    print("-" * 40)
    
    # A = [[3, 1], [1, 2]]，正定厄米矩阵
    A = np.array([
        [3.0, 1.0],
        [1.0, 2.0]
    ])
    b = np.array([1.0, 1.0])
    
    hhl = HHLAlgorithm(A, b)
    
    print(f"矩阵 A:\n{A}")
    print(f"向量 b: {b}")
    print(f"是厄米矩阵: {hhl.validate_hermitian()}")
    
    # HHL 求解
    x_hhl = hhl.hhl_solve()
    x_classical = hhl.classical_solution()
    
    print(f"\nHHL 解: {x_hhl}")
    print(f"经典解: {x_classical}")
    print(f"残差: {hhl.verify_solution(x_hhl):.6f}")
    
    # QK-Means 示例
    print("\n2. 量子 K-Means 聚类")
    print("-" * 40)
    
    np.random.seed(42)
    # 生成三个簇
    data = np.vstack([
        np.random.randn(20, 2) + [2, 2],
        np.random.randn(20, 2) + [-2, 1],
        np.random.randn(20, 2) + [1, -3],
    ])
    
    print(f"数据点: {len(data)}")
    
    qkmeans = QKMeans(n_clusters=3, n_iterations=5)
    print("\n聚类过程：")
    labels = qkmeans.fit(data)
    
    print(f"\n聚类结果: {labels[:10]}...")
    print(f"簇大小: {[sum(labels==i) for i in range(3)]}")
