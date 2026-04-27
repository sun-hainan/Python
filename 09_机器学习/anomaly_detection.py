# -*- coding: utf-8 -*-
"""
算法实现：09_机器学习 / anomaly_detection

本文件实现 anomaly_detection 相关的算法功能。
"""

import numpy as np


class IsolationForest:
    """
     Isolation Forest 实现

    参数:
        n_estimators: 树的数量
        max_samples: 每棵树采样的样本数
        contamination: 异常比例
    """

    def __init__(self, n_estimators=100, max_samples=256, contamination=0.1):
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.contamination = contamination
        self.trees = []
        self.max_depth = 10
        self.features_dim = None

    def _build_tree(self, X, depth=0):
        """递归构建Isolation Tree"""
        n_samples, n_features = X.shape

        if depth >= self.max_depth or n_samples <= 1:
            return {'leaf': True, 'size': n_samples}

        # 随机选择特征和分割点
        feature_idx = np.random.randint(0, n_features)
        min_val = X[:, feature_idx].min()
        max_val = X[:, feature_idx].max()

        if min_val == max_val:
            return {'leaf': True, 'size': n_samples}

        # 随机分割点
        split_val = np.random.uniform(min_val, max_val)

        # 分裂
        left_mask = X[:, feature_idx] < split_val
        right_mask = ~left_mask

        return {
            'leaf': False,
            'feature_idx': feature_idx,
            'split_val': split_val,
            'left': self._build_tree(X[left_mask], depth + 1),
            'right': self._build_tree(X[right_mask], depth + 1),
        }

    def fit(self, X):
        """
        训练

        参数:
            X: 训练数据 (n_samples, n_features)
        """
        self.features_dim = X.shape[1]
        n_samples = X.shape[0]

        # 调整采样数
        sample_size = min(self.max_samples, n_samples)

        # 构建多棵树
        self.trees = []
        for _ in range(self.n_estimators):
            # 随机采样
            indices = np.random.choice(n_samples, sample_size, replace=False)
            X_sample = X[indices]

            # 构建树
            tree = self._build_tree(X_sample)
            self.trees.append(tree)

    def _path_length(self, x, tree, depth=0):
        """计算样本在树中的路径长度"""
        if tree['leaf']:
            # 叶子节点：路径长度 + 均衡因子
            return depth + self._c(tree['size'])

        # 根据分割点向左或右走
        if x[tree['feature_idx']] < tree['split_val']:
            return self._path_length(x, tree['left'], depth + 1)
        else:
            return self._path_length(x, tree['right'], depth + 1)

    def _c(self, n):
        """均衡因子c(n)"""
        if n <= 1:
            return 0
        return 2 * (np.log(n - 1) + 0.5772156649) - (2 * (n - 1) / n)

    def _anomaly_score(self, x):
        """计算单个样本的异常分数"""
        # 在所有树上计算路径长度
        path_lengths = []
        for tree in self.trees:
            h_x = self._path_length(x, tree)
            path_lengths.append(h_x)

        # 平均路径长度
        E_h_x = np.mean(path_lengths)

        # 异常分数
        c_n = self._c(self.max_samples)
        score = 2 ** (-E_h_x / c_n)

        return score

    def score_samples(self, X):
        """
        计算异常分数

        返回:
            scores: 异常分数（越高越异常）
        """
        scores = []
        for x in X:
            score = self._anomaly_score(x)
            scores.append(score)
        return np.array(scores)

    def predict(self, X):
        """
        预测

        返回:
            -1: 异常, 1: 正常
        """
        scores = self.score_samples(X)
        threshold = np.percentile(scores, 100 * (1 - self.contamination))
        return np.where(scores >= threshold, -1, 1)


class OneClassSVM:
    """
    One-Class SVM 实现（简化版）

    使用SVDD（Support Vector Data Description）思想
    找到一个超球体包裹正常数据

    参数:
        kernel: 核函数类型
        gamma: RBF核参数
        nu: 异常比例上界
    """

    def __init__(self, kernel='rbf', gamma=0.1, nu=0.1):
        self.kernel = kernel
        self.gamma = gamma
        self.nu = nu
        self.X_train = None
        self.center = None
        self.radius = None

    def _rbf_kernel(self, X1, X2):
        """RBF核: k(x,y) = exp(-γ * ||x-y||²)"""
        # 简化为计算X1和X2中心点的距离
        if len(X1.shape) == 1:
            X1 = X1.reshape(1, -1)
        if len(X2.shape) == 1:
            X2 = X2.reshape(1, -1)

        dist = np.sqrt(((X1[:, None] - X2) ** 2).sum(axis=2))
        return np.exp(-self.gamma * dist)

    def fit(self, X):
        """
        训练

        参数:
            X: 正常数据 (n_samples, n_features)
        """
        self.X_train = X
        n_samples = X.shape[0]

        # 简化：用数据中心点和到最远点的距离初始化
        self.center = np.mean(X, axis=0)

        # 计算到中心点的距离
        distances = np.linalg.norm(X - self.center, axis=1)

        # 用分位数设置半径
        self.radius = np.percentile(distances, 100 * (1 - self.nu))

        print(f"   One-Class SVM: center shape={self.center.shape}, radius={self.radius:.4f}")

    def decision_function(self, X):
        """
        计算决策函数值

        返回:
            值<0的为异常
        """
        distances = np.linalg.norm(X - self.center, axis=1)
        # 返回到超球体边界的距离
        return self.radius - distances

    def predict(self, X):
        """
        预测

        返回:
            1: 正常, -1: 异常
        """
        scores = self.decision_function(X)
        return np.where(scores < 0, -1, 1)


def test_anomaly_detection():
    """测试异常检测"""
    np.random.seed(42)

    print("=" * 60)
    print("异常检测测试")
    print("=" * 60)

    # 生成正常数据
    n_normal = 500
    n_features = 2

    # 正常数据：中心在(0,0)的正态分布
    X_normal = np.random.randn(n_normal, n_features) * 0.5

    # 异常数据：在外围的点
    n_anomaly = 20
    anomaly_indices = np.random.choice(4, n_anomaly)
    X_anomaly = np.zeros((n_anomaly, n_features))

    for i, idx in enumerate(anomaly_indices):
        angle = np.random.uniform(0, 2 * np.pi)
        if idx == 0:
            # 右侧异常
            X_anomaly[i] = [2.5 + np.random.randn() * 0.2, np.random.randn() * 0.3]
        elif idx == 1:
            # 上方异常
            X_anomaly[i] = [np.random.randn() * 0.3, 2.5 + np.random.randn() * 0.2]
        elif idx == 2:
            # 左侧异常
            X_anomaly[i] = [-2.5 + np.random.randn() * 0.2, np.random.randn() * 0.3]
        else:
            # 下方异常
            X_anomaly[i] = [np.random.randn() * 0.3, -2.5 + np.random.randn() * 0.2]

    # 合并数据
    X = np.vstack([X_normal, X_anomaly])
    y_true = np.array([1] * n_normal + [-1] * n_anomaly)  # 1=正常, -1=异常

    print(f"\n1. 数据信息:")
    print(f"   正常样本: {n_normal}")
    print(f"   异常样本: {n_anomaly}")
    print(f"   特征维度: {n_features}")

    # 测试Isolation Forest
    print("\n2. Isolation Forest:")
    iso_forest = IsolationForest(n_estimators=50, max_samples=256, contamination=0.05)
    iso_forest.fit(X_normal)

    scores_iso = iso_forest.score_samples(X)
    preds_iso = iso_forest.predict(X)

    acc_iso = np.mean(preds_iso == y_true)
    print(f"   准确率: {acc_iso:.4f}")
    print(f"   检测到的异常数: {np.sum(preds_iso == -1)}")

    # 测试One-Class SVM
    print("\n3. One-Class SVM:")
    oc_svm = OneClassSVM(kernel='rbf', gamma=1.0, nu=0.05)
    oc_svm.fit(X_normal)

    scores_ocsvm = oc_svm.decision_function(X)
    preds_ocsvm = oc_svm.predict(X)

    acc_ocsvm = np.mean(preds_ocsvm == y_true)
    print(f"   准确率: {acc_ocsvm:.4f}")
    print(f"   检测到的异常数: {np.sum(preds_ocsvm == -1)}")

    print("\n4. 算法对比:")
    print("   ┌─────────────────────────────────────────────┐")
    print("   │ Isolation Forest:                          │")
    print("   │   - 基于随机分割，异常点隔离路径更短        │")
    print("   │   - 适合大规模数据                           │")
    print("   │   - 对多维数据效果好                        │")
    print("   │ One-Class SVM:                              │")
    print("   │   - 学习一个边界包裹正常数据                │")
    print("   │   - 适合高维小样本数据                      │")
    print("   │   - 需要选择合适的核函数和参数              │")
    print("   └─────────────────────────────────────────────┘")


if __name__ == "__main__":
    test_anomaly_detection()
