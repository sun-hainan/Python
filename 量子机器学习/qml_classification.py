# -*- coding: utf-8 -*-
"""
算法实现：量子机器学习 / qml_classification

本文件实现 qml_classification 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class Classifier_Type(Enum):
    """分类器类型"""
    QUANTUM_KNN = "quantum_knn"
    QUANTUM_DECISION_TREE = "quantum_decision_tree"
    QUANTUM_NAIVE_BAYES = "quantum_naive_bayes"


@dataclass
class Quantum_State_Vector:
    """量子态向量"""
    amplitudes: np.ndarray  # 振幅
    num_qubits: int


class Quantum_KNN:
    """量子最近邻分类器（QKNN）"""
    def __init__(self, k: int = 3, num_qubits: int = 8):
        self.k = k
        self.num_qubits = num_qubits
        self.X_train: Optional[np.ndarray] = None
        self.y_train: Optional[np.ndarray] = None


    def _encode_vector(self, x: np.ndarray) -> np.ndarray:
        """振幅编码"""
        dim = len(x)
        max_dim = 2 ** self.num_qubits
        state = np.zeros(max_dim, dtype=complex)
        state[:min(dim, max_dim)] = x[:min(dim, max_dim)]
        norm = np.linalg.norm(state)
        if norm > 1e-10:
            state /= norm
        else:
            state[0] = 1.0
        return state


    def _quantum_distance(self, x: np.ndarray, y: np.ndarray) -> float:
        """
        计算量子距离（使用SWAP test的变体）
        d²(x,y) = 2(1 - |<x|y>|²)
        """
        state_x = self._encode_vector(x)
        state_y = self._encode_vector(y)
        # 计算内积
        inner_product = np.vdot(state_x, state_y)
        fidelity = np.abs(inner_product) ** 2
        distance = 2 * (1 - fidelity)
        return distance


    def fit(self, X: np.ndarray, y: np.ndarray):
        """训练"""
        self.X_train = X
        self.y_train = y


    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        predictions = []
        for x in X:
            # 计算到所有训练样本的距离
            distances = [self._quantum_distance(x, x_train) for x_train in self.X_train]
            # 找到k个最近邻
            k_nearest_indices = np.argsort(distances)[:self.k]
            k_nearest_labels = self.y_train[k_nearest_indices]
            # 投票
            unique_labels, counts = np.unique(k_nearest_labels, return_counts=True)
            predictions.append(unique_labels[np.argmax(counts)])
        return np.array(predictions)


class Quantum_Decision_Tree:
    """量子决策树分类器（简化）"""
    def __init__(self, max_depth: int = 5):
        self.max_depth = max_depth
        self.tree = None
        self.num_qubits = 6


    def _compute_information_gain(self, X: np.ndarray, y: np.ndarray, feature_idx: int, threshold: float) -> float:
        """计算信息增益"""
        # 简化的信息增益计算
        left_mask = X[:, feature_idx] <= threshold
        right_mask = ~left_mask
        if np.sum(left_mask) == 0 or np.sum(right_mask) == 0:
            return 0
        # 计算熵
        def entropy(mask):
            labels = y[mask]
            if len(labels) == 0:
                return 0
            _, counts = np.unique(labels, return_counts=True)
            probs = counts / len(labels)
            return -np.sum(probs * np.log2(probs + 1e-10))
        parent_entropy = entropy(np.ones(len(y), dtype=bool))
        left_entropy = entropy(left_mask)
        right_entropy = entropy(right_mask)
        n = len(y)
        ig = parent_entropy - (np.sum(left_mask) / n * left_entropy + np.sum(right_mask) / n * right_entropy)
        return ig


    def _build_tree(self, X: np.ndarray, y: np.ndarray, depth: int = 0):
        """递归构建决策树"""
        # 终止条件
        if depth >= self.max_depth or len(np.unique(y)) == 1:
            # 叶节点：多数类
            unique_labels, counts = np.unique(y, return_counts=True)
            return {"leaf": unique_labels[np.argmax(counts)]}
        # 找最佳分裂
        best_ig = -1
        best_split = None
        for feature_idx in range(X.shape[1]):
            for threshold in [np.median(X[:, feature_idx])]:
                ig = self._compute_information_gain(X, y, feature_idx, threshold)
                if ig > best_ig:
                    best_ig = ig
                    best_split = (feature_idx, threshold)
        if best_split is None or best_ig <= 0:
            unique_labels, counts = np.unique(y, return_counts=True)
            return {"leaf": unique_labels[np.argmax(counts)]}
        # 分裂
        feature_idx, threshold = best_split
        left_mask = X[:, feature_idx] <= threshold
        node = {
            "feature": feature_idx,
            "threshold": threshold,
            "left": self._build_tree(X[left_mask], y[left_mask], depth + 1),
            "right": self._build_tree(X[~left_mask], y[~left_mask], depth + 1)
        }
        return node


    def fit(self, X: np.ndarray, y: np.ndarray):
        """训练"""
        self.tree = self._build_tree(X, y)


    def _predict_single(self, x: np.ndarray, node: dict) -> int:
        """预测单个样本"""
        if "leaf" in node:
            return node["leaf"]
        if x[node["feature"]] <= node["threshold"]:
            return self._predict_single(x, node["left"])
        else:
            return self._predict_single(x, node["right"])


    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        return np.array([self._predict_single(x, self.tree) for x in X])


class Quantum_Naive_Bayes:
    """量子朴素贝叶斯分类器（简化）"""
    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha  # 拉普拉斯平滑
        self.classes: Optional[np.ndarray] = None
        self.class_prior: Optional[np.ndarray] = None
        self.feature_probs: Optional[List[np.ndarray]] = None
        self.num_qubits = 6


    def _compute_likelihood(self, x: np.ndarray, mean: np.ndarray, var: np.ndarray) -> float:
        """计算高斯似然（简化）"""
        # 简化的似然计算
        diff = x - mean
        likelihood = np.exp(-diff ** 2 / (2 * var + 1e-10))
        return np.prod(likelihood + 1e-10)


    def fit(self, X: np.ndarray, y: np.ndarray):
        """训练"""
        self.classes, class_counts = np.unique(y, return_counts=True)
        self.class_prior = class_counts / len(y)
        self.feature_probs = []
        for c in self.classes:
            X_c = X[y == c]
            mean = np.mean(X_c, axis=0)
            var = np.var(X_c, axis=0) + self.alpha
            self.feature_probs.append((mean, var))


    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        predictions = []
        for x in X:
            posteriors = []
            for i, c in enumerate(self.classes):
                prior = self.class_prior[i]
                mean, var = self.feature_probs[i]
                likelihood = self._compute_likelihood(x, mean, var)
                posterior = prior * likelihood
                posteriors.append(posterior)
            predictions.append(self.classes[np.argmax(posteriors)])
        return np.array(predictions)


def generate_classification_data() -> Tuple[np.ndarray, np.ndarray]:
    """生成分类数据"""
    np.random.seed(42)
    n = 100
    # 类别1
    X1 = np.random.randn(n // 2, 2) + np.array([0, 0])
    y1 = np.zeros(n // 2)
    # 类别2
    X2 = np.random.randn(n // 2, 2) + np.array([2, 2])
    y2 = np.ones(n // 2)
    X = np.vstack([X1, X2])
    y = np.concatenate([y1, y2])
    return X, y


def basic_test():
    """基本功能测试"""
    print("=== 量子分类算法测试 ===")
    X, y = generate_classification_data()
    print(f"数据: {X.shape}, 类别数: {len(np.unique(y))}")
    # QKNN
    print("\n[量子KNN分类器]")
    qknn = Quantum_KNN(k=3)
    qknn.fit(X, y)
    pred_knn = qknn.predict(X)
    acc_knn = np.mean(pred_knn == y)
    print(f"  准确率: {acc_knn:.2%}")
    # 决策树
    print("\n[量子决策树分类器]")
    qdt = Quantum_Decision_Tree(max_depth=5)
    qdt.fit(X, y)
    pred_dt = qdt.predict(X)
    acc_dt = np.mean(pred_dt == y)
    print(f"  准确率: {acc_dt:.2%}")
    # 朴素贝叶斯
    print("\n[量子朴素贝叶斯分类器]")
    qnb = Quantum_Naive_Bayes(alpha=1.0)
    qnb.fit(X, y)
    pred_nb = qnb.predict(X)
    acc_nb = np.mean(pred_nb == y)
    print(f"  准确率: {acc_nb:.2%}")
    # 对比经典
    print("\n对比经典分类器:")
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.naive_bayes import GaussianNB
    knn = KNeighborsClassifier(n_neighbors=3)
    knn.fit(X, y)
    print(f"  经典KNN: {np.mean(knn.predict(X) == y):.2%}")
    dt = DecisionTreeClassifier(max_depth=5)
    dt.fit(X, y)
    print(f"  经典决策树: {np.mean(dt.predict(X) == y):.2%}")
    nb = GaussianNB()
    nb.fit(X, y)
    print(f"  经典朴素贝叶斯: {np.mean(nb.predict(X) == y):.2%}")


if __name__ == "__main__":
    basic_test()
