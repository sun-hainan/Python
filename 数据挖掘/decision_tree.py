# -*- coding: utf-8 -*-
"""
算法实现：数据挖掘 / decision_tree

本文件实现 decision_tree 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from collections import defaultdict
import math


class DecisionTreeNode:
    """决策树节点"""
    
    def __init__(self, feature_idx: int = None, threshold: float = None,
                 left: 'DecisionTreeNode' = None, right: 'DecisionTreeNode' = None,
                 value: Any = None, is_leaf: bool = False):
        self.feature_idx = feature_idx  # 分裂特征索引
        self.threshold = threshold      # 连续特征的分裂阈值
        self.left = left                # 左子节点
        self.right = right              # 右子节点
        self.value = value              # 叶节点的值（类别或数值）
        self.is_leaf = is_leaf          # 是否为叶节点
        self.n_samples = 0              # 该节点样本数
        self.class_distribution: Dict[Any, int] = {}  # 类别分布


class DecisionTree:
    """
    决策树分类器
    
    参数:
        criterion: 分裂准则 ('gini', 'entropy', 'mse')
        max_depth: 最大深度
        min_samples_split: 分裂所需最小样本数
        min_samples_leaf: 叶节点最小样本数
    """
    
    def __init__(self, criterion: str = 'gini', max_depth: int = 10,
                 min_samples_split: int = 2, min_samples_leaf: int = 1):
        self.criterion = criterion
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        
        self.root: Optional[DecisionTreeNode] = None
        self.n_classes: int = 0
        self.n_features: int = 0
        self.feature_thresholds: Dict[int, float] = {}  # 存储连续特征的阈值
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'DecisionTree':
        """
        训练决策树
        
        参数:
            X: 特征矩阵 (n_samples, n_features)
            y: 目标向量 (n_samples,)
        """
        X = np.asarray(X)
        y = np.asarray(y)
        
        self.n_features = X.shape[1]
        self.n_classes = len(np.unique(y))
        
        # 构建树
        self.root = self._build_tree(X, y, depth=0)
        
        return self
    
    def _gini(self, y: np.ndarray) -> float:
        """计算Gini不纯度"""
        if len(y) == 0:
            return 0.0
        
        counts = defaultdict(int)
        for label in y:
            counts[label] += 1
        
        impurity = 1.0
        n = len(y)
        for count in counts.values():
            p = count / n
            impurity -= p * p
        
        return impurity
    
    def _entropy(self, y: np.ndarray) -> float:
        """计算熵"""
        if len(y) == 0:
            return 0.0
        
        counts = defaultdict(int)
        for label in y:
            counts[label] += 1
        
        n = len(y)
        ent = 0.0
        for count in counts.values():
            p = count / n
            if p > 0:
                ent -= p * math.log2(p)
        
        return ent
    
    def _mse(self, y: np.ndarray) -> float:
        """计算均方误差（用于回归）"""
        if len(y) == 0:
            return 0.0
        return np.var(y)
    
    def _impurity(self, y: np.ndarray) -> float:
        """根据criterion计算不纯度"""
        if self.criterion == 'gini':
            return self._gini(y)
        elif self.criterion == 'entropy':
            return self._entropy(y)
        elif self.criterion == 'mse':
            return self._mse(y)
        return self._gini(y)
    
    def _best_split(self, X: np.ndarray, y: np.ndarray) -> Tuple[Optional[int], Optional[float], float]:
        """
        找到最佳分裂特征和阈值
        
        返回:
            (feature_idx, threshold, impurity_gain)
        """
        n_samples, n_features = X.shape
        
        if n_samples < self.min_samples_split:
            return None, None, 0.0
        
        # 父节点不纯度
        parent_impurity = self._impurity(y)
        
        best_gain = 0.0
        best_feature = None
        best_threshold = None
        
        # 遍历所有特征
        for feature_idx in range(n_features):
            # 获取该特征的唯一值
            values = X[:, feature_idx]
            
            # 如果特征唯一值太多，采样候选阈值
            unique_values = np.unique(values)
            
            if len(unique_values) > 10:
                # 随机采样阈值
                indices = np.random.choice(len(unique_values), min(10, len(unique_values)), replace=False)
                candidates = [unique_values[i] for i in sorted(indices)]
            else:
                candidates = unique_values[:-1]
            
            # 尝试每个候选阈值
            for threshold in candidates:
                # 分裂
                left_mask = X[:, feature_idx] < threshold
                right_mask = ~left_mask
                
                if left_mask.sum() < self.min_samples_leaf or right_mask.sum() < self.min_samples_leaf:
                    continue
                
                # 计算加权不纯度
                left_impurity = self._impurity(y[left_mask])
                right_impurity = self._impurity(y[right_mask])
                
                n_left = left_mask.sum()
                n_right = right_mask.sum()
                n = n_samples
                
                weighted_impurity = (n_left * left_impurity + n_right * right_impurity) / n
                
                gain = parent_impurity - weighted_impurity
                
                if gain > best_gain:
                    best_gain = gain
                    best_feature = feature_idx
                    best_threshold = threshold
        
        return best_feature, best_threshold, best_gain
    
    def _build_tree(self, X: np.ndarray, y: np.ndarray, depth: int) -> DecisionTreeNode:
        """递归构建决策树"""
        n_samples = len(y)
        
        node = DecisionTreeNode()
        node.n_samples = n_samples
        
        # 统计类别分布
        for label in y:
            node.class_distribution[label] = node.class_distribution.get(label, 0) + 1
        
        # 终止条件
        if (depth >= self.max_depth or 
            n_samples < self.min_samples_split or
            len(np.unique(y)) == 1):
            node.is_leaf = True
            node.value = self._most_common_label(y)
            return node
        
        # 找最佳分裂
        feature_idx, threshold, gain = self._best_split(X, y)
        
        if feature_idx is None or gain <= 0:
            node.is_leaf = True
            node.value = self._most_common_label(y)
            return node
        
        # 保存阈值
        self.feature_thresholds[feature_idx] = threshold
        
        # 分裂
        left_mask = X[:, feature_idx] < threshold
        right_mask = ~left_mask
        
        node.feature_idx = feature_idx
        node.threshold = threshold
        node.left = self._build_tree(X[left_mask], y[left_mask], depth + 1)
        node.right = self._build_tree(X[right_mask], y[right_mask], depth + 1)
        
        return node
    
    def _most_common_label(self, y: np.ndarray) -> Any:
        """返回最常见的标签"""
        counts = defaultdict(int)
        for label in y:
            counts[label] += 1
        return max(counts, key=counts.get)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        预测类别
        
        参数:
            X: 特征矩阵 (n_samples, n_features)
        
        返回:
            预测类别 (n_samples,)
        """
        X = np.asarray(X)
        return np.array([self._predict_single(x) for x in X])
    
    def _predict_single(self, x: np.ndarray) -> Any:
        """预测单个样本"""
        node = self.root
        
        while not node.is_leaf:
            if x[node.feature_idx] < node.threshold:
                node = node.left
            else:
                node = node.right
        
        return node.value
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        预测类别概率
        
        返回:
            概率矩阵 (n_samples, n_classes)
        """
        X = np.asarray(X)
        n_samples = X.shape[0]
        
        proba = np.zeros((n_samples, self.n_classes))
        
        for i, x in enumerate(X):
            node = self.root
            
            while not node.is_leaf:
                if x[node.feature_idx] < node.threshold:
                    node = node.left
                else:
                    node = node.right
            
            # 计算类别分布概率
            total = sum(node.class_distribution.values())
            for j, count in node.class_distribution.items():
                proba[i, j] = count / total
        
        return proba
    
    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        计算准确率
        
        参数:
            X: 特征矩阵
            y: 真实标签
        
        返回:
            准确率
        """
        predictions = self.predict(X)
        return np.mean(predictions == y)
    
    def print_tree(self, node: DecisionTreeNode = None, depth: int = 0) -> None:
        """打印树结构"""
        if node is None:
            node = self.root
        
        prefix = "  " * depth
        
        if node.is_leaf:
            print(f"{prefix}Leaf: {node.value} (n={node.n_samples})")
        else:
            print(f"{prefix}Feature_{node.feature_idx} < {node.threshold:.3f} (n={node.n_samples})")
            print(f"{prefix}  Left:")
            self.print_tree(node.left, depth + 2)
            print(f"{prefix}  Right:")
            self.print_tree(node.right, depth + 2)
    
    def get_depth(self) -> int:
        """获取树的深度"""
        return self._get_depth(self.root)
    
    def _get_depth(self, node: DecisionTreeNode) -> int:
        """递归计算深度"""
        if node is None or node.is_leaf:
            return 0
        return 1 + max(self._get_depth(node.left), self._get_depth(node.right))
    
    def get_n_leaves(self) -> int:
        """获取叶节点数"""
        return self._get_n_leaves(self.root)
    
    def _get_n_leaves(self, node: DecisionTreeNode) -> int:
        """递归计算叶节点数"""
        if node is None:
            return 0
        if node.is_leaf:
            return 1
        return self._get_n_leaves(node.left) + self._get_n_leaves(node.right)


class DecisionTreeRegressor(DecisionTree):
    """决策树回归器"""
    
    def __init__(self, max_depth: int = 10, min_samples_split: int = 2,
                 min_samples_leaf: int = 1):
        super().__init__(criterion='mse', max_depth=max_depth,
                         min_samples_split=min_samples_split,
                         min_samples_leaf=min_samples_leaf)
    
    def _most_common_label(self, y: np.ndarray) -> float:
        """返回均值（用于回归）"""
        return np.mean(y)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测数值"""
        X = np.asarray(X)
        return np.array([self._predict_single(x) for x in X])
    
    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """计算R²分数"""
        predictions = self.predict(X)
        y_mean = np.mean(y)
        
        ss_res = np.sum((y - predictions) ** 2)
        ss_tot = np.sum((y - y_mean) ** 2)
        
        if ss_tot == 0:
            return 0.0
        
        return 1 - ss_res / ss_tot


# ==================== 测试代码 ====================
if __name__ == "__main__":
    print("=" * 50)
    print("决策树测试")
    print("=" * 50)
    
    import random
    
    np.random.seed(42)
    random.seed(42)
    
    # ========== 分类测试 ==========
    print("\n--- 分类任务 ---")
    
    # 生成数据：两个类别
    n_samples = 300
    X = np.zeros((n_samples, 2))
    y = np.zeros(n_samples)
    
    # 类别1：中心在(0,0)
    X[:100] = np.random.randn(100, 2) * 0.5
    y[:100] = 0
    
    # 类别2：中心在(2,2)
    X[100:200] = np.random.randn(100, 2) * 0.5 + np.array([2, 2])
    y[100:200] = 1
    
    # 类别3：中心在(0,3)
    X[200:] = np.random.randn(100, 2) * 0.5 + np.array([0, 3])
    y[200:] = 2
    
    # 打乱
    shuffle_idx = np.random.permutation(n_samples)
    X = X[shuffle_idx]
    y = y[shuffle_idx]
    
    # 训练
    tree = DecisionTree(criterion='gini', max_depth=5, min_samples_leaf=5)
    tree.fit(X, y)
    
    # 评估
    accuracy = tree.score(X, y)
    print(f"训练准确率: {accuracy:.2%}")
    print(f"树的深度: {tree.get_depth()}")
    print(f"叶节点数: {tree.get_n_leaves()}")
    
    # 预测示例
    test_points = np.array([[0, 0], [2, 2], [0, 3]])
    predictions = tree.predict(test_points)
    print(f"\n测试点预测:")
    for i, (pt, pred) in enumerate(zip(test_points, predictions)):
        print(f"  点{pt}: 类别{int(pred)}")
    
    # 打印树结构
    print("\n树结构:")
    tree.print_tree()
    
    # ========== 回归测试 ==========
    print("\n--- 回归任务 ---")
    
    # 生成回归数据
    n = 100
    X_reg = np.random.randn(n, 1)
    y_reg = X_reg[:, 0] ** 2 + 0.5 * np.random.randn(n)
    
    # 训练回归树
    reg_tree = DecisionTreeRegressor(max_depth=4)
    reg_tree.fit(X_reg, y_reg)
    
    # 评估
    r2 = reg_tree.score(X_reg, y_reg)
    print(f"R² 分数: {r2:.4f}")
    print(f"树深度: {reg_tree.get_depth()}")
    
    # 预测
    test_x = np.array([[-2], [-1], [0], [1], [2]])
    predictions = reg_tree.predict(test_x)
    actual = test_x[:, 0] ** 2
    
    print(f"\n回归预测:")
    print(f"{'x':>8} | {'预测':>10} | {'真实':>10} | {'误差':>10}")
    print("-" * 50)
    for x, pred, act in zip(test_x[:, 0], predictions, actual):
        print(f"{x:>8.1f} | {pred:>10.4f} | {act:>10.4f} | {abs(pred-act):>10.4f}")
    
    # ========== 性能对比 ==========
    print("\n" + "=" * 50)
    print("决策树 vs sklearn (如果可用)")
    print("=" * 50)
    
    try:
        from sklearn.tree import DecisionTreeClassifier as SklearnTree
        from sklearn.datasets import load_iris
        
        # 使用鸢尾花数据集
        iris = load_iris()
        X_iris = iris.data
        y_iris = iris.target
        
        # 打乱
        shuffle_idx = np.random.permutation(len(y_iris))
        X_iris = X_iris[shuffle_idx]
        y_iris = y_iris[shuffle_idx]
        
        # 划分训练测试
        split = int(len(y_iris) * 0.8)
        X_train, X_test = X_iris[:split], X_iris[split:]
        y_train, y_test = y_iris[:split], y_iris[split:]
        
        # 我们的实现
        our_tree = DecisionTree(max_depth=10)
        our_tree.fit(X_train, y_train)
        our_acc = our_tree.score(X_test, y_test)
        
        # sklearn实现
        sklearn_tree = SklearnTree(max_depth=10)
        sklearn_tree.fit(X_train, y_train)
        sklearn_acc = sklearn_tree.score(X_test, y_test)
        
        print(f"\n鸢尾花数据集 ({len(y_iris)} 样本, {X_iris.shape[1]} 特征)")
        print(f"我们的决策树准确率: {our_acc:.2%}")
        print(f"sklearn决策树准确率: {sklearn_acc:.2%}")
        print(f"我们的树深度: {our_tree.get_depth()}")
        
    except ImportError:
        print("sklearn未安装，跳过对比")
    
    # ========== 大规模测试 ==========
    print("\n--- 大规模性能测试 ---")
    
    import time
    
    n_large = 5000
    X_large = np.random.randn(n_large, 10)
    y_large = (X_large[:, 0] + X_large[:, 1] > 0).astype(int)
    
    start = time.time()
    large_tree = DecisionTree(max_depth=10)
    large_tree.fit(X_large, y_large)
    elapsed = time.time() - start
    
    accuracy = large_tree.score(X_large, y_large)
    
    print(f"训练 {n_large} 样本, {X_large.shape[1]} 特征")
    print(f"耗时: {elapsed:.3f}秒")
    print(f"准确率: {accuracy:.2%}")
    print(f"树深度: {large_tree.get_depth()}")
    print(f"叶节点数: {large_tree.get_n_leaves()}")
