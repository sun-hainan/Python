# -*- coding: utf-8 -*-
"""
算法实现：数据挖掘 / feature_importance

本文件实现 feature_importance 相关的算法功能。
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Callable
from collections import defaultdict
import random


class FeatureImportance:
    """
    特征重要性基类
    """
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'FeatureImportance':
        raise NotImplementedError
    
    def get_importance(self) -> np.ndarray:
        raise NotImplementedError


class TreeBasedImportance(FeatureImportance):
    """
    基于决策树的特征重要性
    
    Gini Importance:
    importance_j = Σ_{node where feature j splits} n_node * impurity_node - 
                   n_left * impurity_left - n_right * impurity_right
    """
    
    def __init__(self, max_depth: int = 5, min_samples_split: int = 10):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        
        self.n_features = 0
        self.feature_importances_: Optional[np.ndarray] = None
        self.tree_: Optional['TreeNode'] = None
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'TreeBasedImportance':
        """训练"""
        X = np.asarray(X)
        y = np.asarray(y)
        
        self.n_features = X.shape[1]
        self.feature_importances_ = np.zeros(self.n_features)
        
        # 构建树
        self.tree_ = self._build_tree(X, y, depth=0)
        
        # 累积特征重要性
        self._accumulate_importance(self.tree_)
        
        # 归一化
        total = self.feature_importances_.sum()
        if total > 0:
            self.feature_importances_ /= total
        
        return self
    
    def _gini(self, y: np.ndarray) -> float:
        """计算Gini不纯度"""
        if len(y) == 0:
            return 0.0
        
        counts = defaultdict(int)
        for label in y:
            counts[label] += 1
        
        impurity = 1.0
        for count in counts.values():
            p = count / len(y)
            impurity -= p * p
        
        return impurity
    
    def _best_split(self, X: np.ndarray, y: np.ndarray) -> Tuple[Optional[int], Optional[float], float]:
        """找到最佳分裂特征和值"""
        best_gain = 0.0
        best_feature = None
        best_value = None
        
        current_gini = self._gini(y)
        n_samples = len(y)
        
        for feature_idx in range(X.shape[1]):
            # 获取该特征的所有唯一值
            values = np.unique(X[:, feature_idx])
            
            for value in values:
                # 分裂
                left_mask = X[:, feature_idx] < value
                right_mask = ~left_mask
                
                if left_mask.sum() == 0 or right_mask.sum() == 0:
                    continue
                
                # 计算加权Gini
                left_gini = self._gini(y[left_mask])
                right_gini = self._gini(y[right_mask])
                
                weighted_gini = (left_mask.sum() * left_gini + 
                              right_mask.sum() * right_gini) / n_samples
                
                gain = current_gini - weighted_gini
                
                if gain > best_gain:
                    best_gain = gain
                    best_feature = feature_idx
                    best_value = value
        
        return best_feature, best_value, best_gain
    
    def _build_tree(self, X: np.ndarray, y: np.ndarray, depth: int) -> Optional['TreeNode']:
        """递归构建决策树"""
        n_samples = len(y)
        
        # 终止条件
        if (depth >= self.max_depth or 
            n_samples < self.min_samples_split or
            len(np.unique(y)) == 1):
            # 叶节点
            return TreeNode(value=self._most_common_label(y))
        
        # 找最佳分裂
        feature_idx, value, gain = self._best_split(X, y)
        
        if feature_idx is None or gain <= 0:
            return TreeNode(value=self._most_common_label(y))
        
        # 分裂
        left_mask = X[:, feature_idx] < value
        right_mask = ~left_mask
        
        left_child = self._build_tree(X[left_mask], y[left_mask], depth + 1)
        right_child = self._build_tree(X[right_mask], y[right_mask], depth + 1)
        
        return TreeNode(
            feature=feature_idx,
            value=value,
            gain=gain,
            n_samples=n_samples,
            left=left_child,
            right=right_child
        )
    
    def _most_common_label(self, y: np.ndarray) -> int:
        """返回最常见的标签"""
        counts = defaultdict(int)
        for label in y:
            counts[label] += 1
        return max(counts, key=counts.get)
    
    def _accumulate_importance(self, node: 'TreeNode', weight: float = 1.0) -> None:
        """递归累积特征重要性"""
        if node is None or node.is_leaf:
            return
        
        # 该节点的重要性 = n_samples * gain
        importance = node.n_samples * node.gain * weight
        self.feature_importances_[node.feature] += importance
        
        # 递归子节点
        self._accumulate_importance(node.left, weight * 0.5)
        self._accumulate_importance(node.right, weight * 0.5)
    
    def get_importance(self) -> np.ndarray:
        """获取特征重要性"""
        return self.feature_importances_


class TreeNode:
    """决策树节点"""
    
    def __init__(self, feature: int = None, value: float = None, 
                 gain: float = 0.0, n_samples: int = 0,
                 left: 'TreeNode' = None, right: 'TreeNode' = None):
        self.feature = feature
        self.value = value
        self.gain = gain
        self.n_samples = n_samples
        self.left = left
        self.right = right
    
    @property
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None


class PermutationImportance:
    """
    排列重要性
    
    步骤：
    1. 在测试集上评估模型性能
    2. 对每个特征，随机打乱其值
    3. 重新评估性能
    4. 重要性 = 原始性能 - 打乱后性能
    """
    
    def __init__(self, n_repeats: int = 10):
        self.n_repeats = n_repeats
        
        self.feature_importances_: Optional[np.ndarray] = None
        self.feature_importances_std_: Optional[np.ndarray] = None
    
    def fit(self, X: np.ndarray, y: np.ndarray, 
            scorer: Callable[[np.ndarray, np.ndarray], float] = None) -> 'PermutationImportance':
        """
        计算排列重要性
        
        参数:
            X: 特征矩阵
            y: 目标值
            scorer: 评分函数，默认为分类准确率
        """
        X = np.asarray(X)
        y = np.asarray(y)
        
        if scorer is None:
            scorer = self._accuracy
        
        n_samples, n_features = X.shape
        self.feature_importances_ = np.zeros(n_features)
        self.feature_importances_std_ = np.zeros(n_features)
        
        # 原始性能
        baseline_score = scorer(X, y)
        
        # 对每个特征
        for feature_idx in range(n_features):
            scores = []
            
            for _ in range(self.n_repeats):
                # 打乱该特征
                X_permuted = X.copy()
                np.random.shuffle(X_permuted[:, feature_idx])
                
                # 重新评分
                permuted_score = scorer(X_permuted, y)
                scores.append(baseline_score - permuted_score)
            
            # 平均
            self.feature_importances_[feature_idx] = np.mean(scores)
            self.feature_importances_std_[feature_idx] = np.std(scores)
        
        return self
    
    def _accuracy(self, X: np.ndarray, y: np.ndarray) -> float:
        """简单分类准确率"""
        return np.mean(X[:, 0] > 0.5)  # 简化
    
    def get_importance(self) -> np.ndarray:
        """获取特征重要性"""
        return self.feature_importances_


class CorrelationImportance:
    """
    基于相关的特征重要性
    
    计算每个特征与目标变量的相关系数绝对值
    """
    
    def __init__(self):
        self.feature_importances_: Optional[np.ndarray] = None
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'CorrelationImportance':
        """计算与目标的相关性"""
        X = np.asarray(X)
        y = np.asarray(y)
        
        n_features = X.shape[1]
        self.feature_importances_ = np.zeros(n_features)
        
        # 确保y是向量
        if len(y.shape) > 1:
            y = y.ravel()
        
        for i in range(n_features):
            corr = self._pearson_correlation(X[:, i], y)
            self.feature_importances_[i] = abs(corr)
        
        # 归一化
        total = self.feature_importances_.sum()
        if total > 0:
            self.feature_importances_ /= total
        
        return self
    
    def _pearson_correlation(self, x: np.ndarray, y: np.ndarray) -> float:
        """计算Pearson相关系数"""
        x_mean = x.mean()
        y_mean = y.mean()
        
        numerator = ((x - x_mean) * (y - y_mean)).sum()
        denominator = np.sqrt(((x - x_mean) ** 2).sum() * ((y - y_mean) ** 2).sum())
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def get_importance(self) -> np.ndarray:
        """获取特征重要性"""
        return self.feature_importances_


class SHAPImportance:
    """
    简化版SHAP重要性
    
    使用边际效应估计每个特征的贡献
    """
    
    def __init__(self, n_samples: int = 100):
        self.n_samples = n_samples
        self.feature_importances_: Optional[np.ndarray] = None
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'SHAPImportance':
        """计算SHAP-like重要性"""
        X = np.asarray(X)
        y = np.asarray(y)
        
        n_samples, n_features = X.shape
        self.feature_importances_ = np.zeros(n_features)
        
        # 使用随机采样的方式估计边际效应
        for _ in range(self.n_samples):
            idx1, idx2 = np.random.choice(n_samples, 2, replace=False)
            
            x1 = X[idx1]
            x2 = X[idx2]
            
            for f in range(n_features):
                # 打乱单个特征
                x_shuffled = x1.copy()
                x_shuffled[f] = x2[f]
                
                # 简化的SHAP值估计
                # 实际应该使用更复杂的博弈论方法
                self.feature_importances_[f] += abs(y[idx1] - y[idx2]) / self.n_samples
        
        # 归一化
        total = self.feature_importances_.sum()
        if total > 0:
            self.feature_importances_ /= total
        
        return self
    
    def get_importance(self) -> np.ndarray:
        """获取特征重要性"""
        return self.feature_importances_


# ==================== 测试代码 ====================
if __name__ == "__main__":
    print("=" * 50)
    print("特征重要性分析测试")
    print("=" * 50)
    
    import random
    
    np.random.seed(42)
    random.seed(42)
    
    # 生成测试数据
    n_samples = 500
    n_features = 10
    
    # 特征：前3个与目标相关，后面不相关
    X = np.random.randn(n_samples, n_features)
    
    # 生成目标：主要受前3个特征影响
    y = (0.5 * X[:, 0] + 0.3 * X[:, 1] + 0.2 * X[:, 2] + 
         0.1 * np.random.randn(n_samples) > 0).astype(int)
    
    feature_names = [f"feature_{i}" for i in range(n_features)]
    
    # ========== 树基重要性 ==========
    print("\n--- 基于决策树的特征重要性 ---")
    
    tree_imp = TreeBasedImportance(max_depth=5)
    tree_imp.fit(X, y)
    
    print(f"{'特征':>12} | {'重要性':>10}")
    print("-" * 30)
    
    importances = tree_imp.get_importance()
    sorted_idx = np.argsort(importances)[::-1]
    
    for idx in sorted_idx:
        bar_len = int(importances[idx] * 40)
        bar = '█' * bar_len
        print(f"{feature_names[idx]:>12} | {importances[idx]:>8.4f} {bar}")
    
    # ========== 相关性重要性 ==========
    print("\n--- 基于相关性的特征重要性 ---")
    
    corr_imp = CorrelationImportance()
    corr_imp.fit(X, y)
    
    print(f"{'特征':>12} | {'重要性':>10}")
    print("-" * 30)
    
    importances = corr_imp.get_importance()
    sorted_idx = np.argsort(importances)[::-1]
    
    for idx in sorted_idx:
        bar_len = int(importances[idx] * 40)
        bar = '█' * bar_len
        print(f"{feature_names[idx]:>12} | {importances[idx]:>8.4f} {bar}")
    
    # ========== 排列重要性 ==========
    print("\n--- 排列重要性 (简化版) ---")
    
    # 使用一个简单的预测器
    def simple_predict(X):
        return (X[:, 0] > 0).astype(int)
    
    def simple_scorer(X, y):
        return np.mean(simple_predict(X) == y)
    
    perm_imp = PermutationImportance(n_repeats=5)
    perm_imp.fit(X, y, scorer=simple_scorer)
    
    print(f"{'特征':>12} | {'重要性':>10} | {'标准差':>10}")
    print("-" * 40)
    
    importances = perm_imp.get_importance()
    std = perm_imp.feature_importances_std_
    sorted_idx = np.argsort(importances)[::-1]
    
    for idx in sorted_idx[:5]:
        bar_len = int(importances[idx] * 40)
        bar = '█' * bar_len
        print(f"{feature_names[idx]:>12} | {importances[idx]:>8.4f} {bar} ±{std[idx]:.4f}")
    
    # ========== SHAP重要性 ==========
    print("\n--- SHAP-like 重要性 ---")
    
    shap_imp = SHAPImportance(n_samples=100)
    shap_imp.fit(X, y)
    
    print(f"{'特征':>12} | {'重要性':>10}")
    print("-" * 30)
    
    importances = shap_imp.get_importance()
    sorted_idx = np.argsort(importances)[::-1]
    
    for idx in sorted_idx:
        bar_len = int(importances[idx] * 40)
        bar = '█' * bar_len
        print(f"{feature_names[idx]:>12} | {importances[idx]:>8.4f} {bar}")
    
    # ========== 对比总结 ==========
    print("\n" + "=" * 50)
    print("特征重要性对比总结")
    print("=" * 50)
    
    methods = [
        ("树基", TreeBasedImportance().fit(X, y).get_importance()),
        ("相关性", CorrelationImportance().fit(X, y).get_importance()),
        ("SHAP-like", SHAPImportance().fit(X, y).get_importance()),
    ]
    
    print(f"\n{'特征':>12} | {'树基':>8} | {'相关性':>8} | {'SHAP':>8}")
    print("-" * 50)
    
    for idx in sorted_idx[:5]:
        row = f"{feature_names[idx]:>12}"
        for name, imp in methods:
            row += f" | {imp[idx]:>8.4f}"
        print(row)
