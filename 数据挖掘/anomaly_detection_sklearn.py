# -*- coding: utf-8 -*-
"""
算法实现：数据挖掘 / anomaly_detection_sklearn

本文件实现 anomaly_detection_sklearn 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Optional, Dict
from collections import defaultdict
import math


class IsolationForest:
    """
    Isolation Forest
    
    核心思想：
    - 随机选择特征和切分点
    - 异常点路径短，容易被隔离
    - 路径长度用于衡量异常程度
    
    参数:
        n_estimators: 树的数量
        max_samples: 每棵树采样的样本数
        contamination: 异常比例估计
        random_state: 随机种子
    """
    
    def __init__(self, n_estimators: int = 100, max_samples: int = 256,
                 contamination: float = 0.1, random_state: int = 42):
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.contamination = contamination
        self.random_state = random_state
        
        self.trees: List['IsolationTree'] = []
        self.threshold: Optional[float] = None
        self.n_features = 0
    
    def fit(self, X: np.ndarray) -> 'IsolationForest':
        """
        训练模型
        
        参数:
            X: 训练数据 (n_samples, n_features)
        """
        np.random.seed(self.random_state)
        X = np.asarray(X)
        self.n_features = X.shape[1]
        
        # 构建孤立森林
        self.trees = []
        n_samples = X.shape[0]
        
        # 样本采样数
        sample_size = min(self.max_samples, n_samples)
        
        for _ in range(self.n_estimators):
            # 随机采样
            indices = np.random.choice(n_samples, sample_size, replace=False)
            X_sample = X[indices]
            
            # 构建树
            tree = IsolationTree(max_height=12)
            tree.build(X_sample)
            self.trees.append(tree)
        
        # 计算异常分数阈值
        self._compute_threshold(X)
        
        return self
    
    def _compute_threshold(self, X: np.ndarray) -> None:
        """计算异常分数阈值"""
        scores = self.decision_function(X)
        
        # 根据污染率设置阈值
        self.threshold = np.percentile(scores, self.contamination * 100)
    
    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """
        计算异常分数
        
        返回:
            异常分数（越小越异常）
        """
        X = np.asarray(X)
        n_samples = X.shape[0]
        
        scores = np.zeros(n_samples)
        
        for tree in self.trees:
            # 计算每个样本在树中的路径长度
            for i, x in enumerate(X):
                scores[i] += tree.path_length(x)
        
        # 归一化
        c = 2 * (math.log(self.max_samples - 1) + 0.5772156649)
        scores = 2 ** (-scores / (self.n_estimators * c))
        
        return scores
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        预测
        
        返回:
            1: 正常
            -1: 异常
        """
        scores = self.decision_function(X)
        return np.where(scores < self.threshold, -1, 1)


class IsolationTree:
    """孤立树节点"""
    
    def __init__(self, max_height: int = 10, current_height: int = 0):
        self.max_height = max_height
        self.current_height = current_height
        self.left: Optional['IsolationTree'] = None
        self.right: Optional['IsolationTree'] = None
        self.split_feature: Optional[int] = None
        self.split_value: Optional[float] = None
        self.is_leaf = False
        self.size = 0
    
    def build(self, X: np.ndarray) -> None:
        """构建孤立树"""
        self.size = len(X)
        n_samples, n_features = X.shape
        
        # 终止条件
        if (self.current_height >= self.max_height or 
            n_samples <= 1 or
            len(set(map(tuple, X))) <= 1):
            self.is_leaf = True
            return
        
        # 随机选择特征和切分值
        self.split_feature = np.random.randint(0, n_features)
        min_val = X[:, self.split_feature].min()
        max_val = X[:, self.split_feature].max()
        
        if min_val == max_val:
            self.is_leaf = True
            return
        
        self.split_value = np.random.uniform(min_val, max_val)
        
        # 分裂
        left_mask = X[:, self.split_feature] < self.split_value
        right_mask = ~left_mask
        
        if left_mask.sum() == 0 or right_mask.sum() == 0:
            self.is_leaf = True
            return
        
        self.left = IsolationTree(self.max_height, self.current_height + 1)
        self.right = IsolationTree(self.max_height, self.current_height + 1)
        
        self.left.build(X[left_mask])
        self.right.build(X[right_mask])
    
    def path_length(self, x: np.ndarray) -> float:
        """计算点到叶节点的路径长度"""
        if self.is_leaf:
            # 叶节点返回路径长度
            if self.size <= 1:
                return self.current_height
            return self.current_height + 2 * (
                math.log(self.size - 1) + 0.5772156649
            ) - 2 * (self.size - 1) / self.size
        
        if x[self.split_feature] < self.split_value:
            return 1 + self.left.path_length(x)
        else:
            return 1 + self.right.path_length(x)


class LocalOutlierFactor:
    """
    Local Outlier Factor (LOF)
    
    核心思想：
    - 计算每个点到k个最近邻的距离（k-距离）
    - 计算每个点的局部可达密度
    - LOF = 点的局部可达密度 / 邻域内点的平均局部可达密度
    - LOF ≈ 1 正常，LOF >> 1 异常
    """
    
    def __init__(self, n_neighbors: int = 20, contamination: float = 0.1):
        self.n_neighbors = n_neighbors
        self.contamination = contamination
        
        self.X_train: Optional[np.ndarray] = None
        self.threshold: Optional[float] = None
    
    def fit(self, X: np.ndarray) -> 'LocalOutlierFactor':
        """训练（实际上是存储训练数据）"""
        X = np.asarray(X)
        self.X_train = X
        return self
    
    def _k_distance(self, x: np.ndarray) -> Tuple[float, List[int]]:
        """计算k-距离和k个最近邻"""
        distances = np.linalg.norm(self.X_train - x, axis=1)
        
        # 排除自身
        sorted_indices = np.argsort(distances)
        k_neighbors = sorted_indices[:self.n_neighbors + 1]
        
        # k-距离是第k个邻居的距离
        k_dist = distances[k_neighbors[self.n_neighbors]]
        
        return k_dist, k_neighbors[1:]  # 排除自身
    
    def _lrd(self, x: np.ndarray) -> float:
        """局部可达密度"""
        k_dist, k_neighbors = self._k_distance(x)
        
        if k_dist == 0:
            return 0.0
        
        # 可达距离
        reach_dist = []
        for neighbor_idx in k_neighbors:
            neighbor = self.X_train[neighbor_idx]
            neighbor_k_dist, _ = self._k_distance(neighbor)
            reach_dist.append(max(k_dist, np.linalg.norm(x - neighbor)))
        
        if sum(reach_dist) == 0:
            return 0.0
        
        return self.n_neighbors / sum(reach_dist)
    
    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """计算LOF分数"""
        X = np.asarray(X)
        n_samples = X.shape[0]
        
        lof_scores = np.zeros(n_samples)
        
        for i, x in enumerate(X):
            k_dist, k_neighbors = self._k_distance(x)
            
            # 计算邻居的lrd
            lrd_neighbors = []
            for neighbor_idx in k_neighbors:
                lrd_neighbors.append(self._lrd(self.X_train[neighbor_idx]))
            
            lrd_x = self._lrd(x)
            
            if lrd_x > 0 and sum(lrd_neighbors) > 0:
                lof_scores[i] = sum(lrd_neighbors) / (self.n_neighbors * lrd_x)
            else:
                lof_scores[i] = 1.0
        
        # 归一化
        lof_scores = 1.0 / (1.0 + lof_scores)
        
        return lof_scores
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        scores = self.decision_function(X)
        
        if self.threshold is None:
            self.threshold = np.percentile(scores, self.contamination * 100)
        
        return np.where(scores < self.threshold, -1, 1)


class OneClassSVM:
    """
    One-Class SVM 简化实现
    
    核心思想：
    - 找到包含所有正常数据点的最小超球面
    - 或找到最大间隔分类超平面
    
    注意：这是一个简化实现，实际应使用libsvm
    """
    
    def __init__(self, kernel: str = 'rbf', nu: float = 0.1, gamma: float = 0.1):
        self.kernel = kernel
        self.nu = nu  # 上界分数（异常比例）和下界支持向量分数
        self.gamma = gamma
        
        self.support_vectors: Optional[np.ndarray] = None
        self.alpha: Optional[np.ndarray] = None
        self.rho: float = 0.0
    
    def fit(self, X: np.ndarray) -> 'OneClassSVM':
        """训练"""
        # 简化：存储数据和支持向量
        X = np.asarray(X)
        n_samples = X.shape[0]
        
        # 选择支持向量（随机选择约 nu * n_samples 个）
        n_sv = max(1, int(self.nu * n_samples))
        
        indices = np.random.choice(n_samples, n_sv, replace=False)
        self.support_vectors = X[indices]
        self.alpha = np.ones(n_sv) * (1.0 / n_sv)
        
        # 简化的偏移量
        self.rho = self.nu * n_samples / n_sv
        
        return self
    
    def _kernel(self, x1: np.ndarray, x2: np.ndarray) -> float:
        """核函数"""
        if self.kernel == 'rbf':
            diff = x1 - x2
            return np.exp(-self.gamma * np.dot(diff, diff))
        elif self.kernel == 'linear':
            return np.dot(x1, x2)
        return 0.0
    
    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """计算决策函数值"""
        X = np.asarray(X)
        n_samples = X.shape[0]
        
        scores = np.zeros(n_samples)
        
        for i, x in enumerate(X):
            f = 0.0
            for j, sv in enumerate(self.support_vectors):
                f += self.alpha[j] * self._kernel(x, sv)
            scores[i] = f - self.rho
        
        return scores
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        scores = self.decision_function(X)
        return np.where(scores < 0, -1, 1)


# ==================== 测试代码 ====================
if __name__ == "__main__":
    print("=" * 50)
    print("异常检测算法测试")
    print("=" * 50)
    
    import random
    
    np.random.seed(42)
    
    # 生成测试数据
    # 正常数据：中心在(0,0)的高斯分布
    n_normal = 500
    normal_data = np.random.randn(n_normal, 2) * 0.5
    
    # 异常数据：远离中心的点
    n_anomaly = 20
    anomaly_data = np.random.randn(n_anomaly, 2) * 3 + np.array([3, 3])
    
    # 合并
    X_train = normal_data[:400]
    X_test = np.vstack([normal_data[400:], anomaly_data[:10]])
    y_true = np.array([1] * 100 + [-1] * 10)
    
    print(f"\n训练数据: {len(X_train)} 样本")
    print(f"测试数据: {len(X_test)} 样本 (含10个异常)")
    
    # ========== Isolation Forest ==========
    print("\n--- Isolation Forest ---")
    
    iforest = IsolationForest(n_estimators=100, contamination=0.05)
    iforest.fit(X_train)
    
    y_pred = iforest.predict(X_test)
    accuracy = np.mean(y_pred == y_true)
    
    print(f"准确率: {accuracy:.2%}")
    print(f"检测到的异常数: {(y_pred == -1).sum()}")
    
    # ========== Local Outlier Factor ==========
    print("\n--- Local Outlier Factor ---")
    
    lof = LocalOutlierFactor(n_neighbors=20, contamination=0.05)
    lof.fit(X_train)
    
    y_pred = lof.predict(X_test)
    accuracy = np.mean(y_pred == y_true)
    
    print(f"准确率: {accuracy:.2%}")
    print(f"检测到的异常数: {(y_pred == -1).sum()}")
    
    # ========== One-Class SVM ==========
    print("\n--- One-Class SVM ---")
    
    ocsvm = OneClassSVM(kernel='rbf', nu=0.05, gamma=0.5)
    ocsvm.fit(X_train)
    
    y_pred = ocsvm.predict(X_test)
    accuracy = np.mean(y_pred == y_true)
    
    print(f"准确率: {accuracy:.2%}")
    print(f"检测到的异常数: {(y_pred == -1).sum()}")
    
    # ========== 异常分数对比 ==========
    print("\n--- 异常分数对比 ---")
    
    if_scores = iforest.decision_function(X_test)
    lof_scores = lof.decision_function(X_test)
    svm_scores = ocsvm.decision_function(X_test)
    
    print(f"{'样本':>8} | {'IF分数':>10} | {'LOF分数':>10} | {'OCSVM分数':>12} | {'真实标签':>8}")
    print("-" * 60)
    
    for i in range(min(15, len(X_test))):
        print(f"{i:>8} | {if_scores[i]:>10.4f} | {lof_scores[i]:>10.4f} | {svm_scores[i]:>12.4f} | {y_true[i]:>8}")
    
    # ========== 性能测试 ==========
    print("\n" + "=" * 50)
    print("性能测试")
    print("=" * 50)
    
    import time
    
    # 大规模数据
    n_large = 10000
    X_large = np.random.randn(n_large, 10)
    
    # 添加一些异常
    anomaly_idx = np.random.choice(n_large, 100, replace=False)
    X_large[anomaly_idx] = X_large[anomaly_idx] * 5 + 10
    
    # IF性能
    start = time.time()
    iforest2 = IsolationForest(n_estimators=100, contamination=0.01)
    iforest2.fit(X_large)
    scores = iforest2.decision_function(X_large)
    if_time = time.time() - start
    
    print(f"Isolation Forest: {n_large}样本, 耗时{if_time:.3f}秒")
    print(f"异常分数范围: [{scores.min():.4f}, {scores.max():.4f}]")
