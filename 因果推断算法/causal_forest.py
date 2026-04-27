# -*- coding: utf-8 -*-
"""
算法实现：因果推断算法 / causal_forest

本文件实现 causal_forest 相关的算法功能。
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
import math


class CausalTree:
    """
    因果树
    
    用于因果推断的决策树
    """
    
    def __init__(self, min_leaf: int = 20, max_depth: int = 5):
        self.min_leaf = min_leaf
        self.max_depth = max_depth
        self.tree = None
        self.effect = None
    
    def fit(self, X: np.ndarray, T: np.ndarray, Y: np.ndarray):
        """
        拟合因果树
        
        Args:
            X: 协变量
            T: 处理指示
            Y: 结果
        """
        n = len(Y)
        
        # 构建树
        self.tree = self._build_tree(X, T, Y, depth=0)
    
    def _build_tree(self, X: np.ndarray, T: np.ndarray, Y: np.ndarray, 
                    depth: int) -> dict:
        """递归构建树"""
        n, d = X.shape
        
        # 停止条件
        if n < self.min_leaf or depth >= self.max_depth:
            return self._make_leaf(T, Y)
        
        # 找最佳分裂
        best_split = self._find_best_split(X, T, Y)
        
        if best_split is None:
            return self._make_leaf(T, Y)
        
        # 分裂
        left_mask = X[:, best_split['feature']] <= best_split['threshold']
        right_mask = ~left_mask
        
        return {
            'feature': best_split['feature'],
            'threshold': best_split['threshold'],
            'left': self._build_tree(X[left_mask], T[left_mask], Y[left_mask], depth+1),
            'right': self._build_tree(X[right_mask], T[right_mask], Y[right_mask], depth+1)
        }
    
    def _find_best_split(self, X: np.ndarray, T: np.ndarray, Y: np.ndarray):
        """找最佳分裂"""
        n, d = X.shape
        best_gain = -float('inf')
        best_split = None
        
        for j in range(d):
            thresholds = np.percentile(X[:, j], [25, 50, 75])
            
            for t in thresholds:
                left_mask = X[:, j] <= t
                right_mask = ~left_mask
                
                if left_mask.sum() < self.min_leaf or right_mask.sum() < self.min_leaf:
                    continue
                
                gain = self._honest_gain(T, Y, left_mask, right_mask)
                
                if gain > best_gain:
                    best_gain = gain
                    best_split = {'feature': j, 'threshold': t}
        
        return best_split
    
    def _honest_gain(self, T: np.ndarray, Y: np.ndarray, 
                     left_mask: np.ndarray, right_mask: np.ndarray) -> float:
        """
        诚实分裂增益
        
        使用样本外估计减少过拟合
        """
        # 简化的增益计算
        n = len(Y)
        
        # 左子节点的估计
        tau_left = self._estimate_effect(T[left_mask], Y[left_mask])
        
        # 右子节点的估计
        tau_right = self._estimate_effect(T[right_mask], Y[right_mask])
        
        # 估计增益（简化）
        gain = (tau_right - tau_left) ** 2
        
        return gain
    
    def _estimate_effect(self, T: np.ndarray, Y: np.ndarray) -> float:
        """估计处理效应"""
        if T.sum() == 0 or (1 - T).sum() == 0:
            return 0.0
        
        # IPW估计
        p = T.mean()
        Y1 = Y[T == 1].mean()
        Y0 = Y[T == 0].mean()
        
        return Y1 - Y0
    
    def _make_leaf(self, T: np.ndarray, Y: np.ndarray) -> dict:
        """创建叶子节点"""
        tau = self._estimate_effect(T, Y)
        n = len(Y)
        
        # 方差估计（简化）
        var = 0.0
        
        return {'leaf': True, 'effect': tau, 'n': n, 'var': var}
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        预测处理效应和方差
        
        Returns:
            (effects, standard_errors)
        """
        effects = np.zeros(len(X))
        ses = np.zeros(len(X))
        
        for i in range(len(X)):
            node = self.tree
            while not node.get('leaf', False):
                if X[i, node['feature']] <= node['threshold']:
                    node = node['left']
                else:
                    node = node['right']
            
            effects[i] = node['effect']
            ses[i] = np.sqrt(node['var'] / node['n'])
        
        return effects, ses


class CausalForest:
    """
    因果森林
    
    多棵因果树的集成
    """
    
    def __init__(self, n_estimators: int = 100, min_leaf: int = 20, 
                 max_depth: int = 5):
        self.n_estimators = n_estimators
        self.min_leaf = min_leaf
        self.max_depth = max_depth
        self.trees = []
    
    def fit(self, X: np.ndarray, T: np.ndarray, Y: np.ndarray):
        """
        拟合因果森林
        """
        # 拟合多棵树
        for _ in range(self.n_estimators):
            tree = CausalTree(min_leaf=self.min_leaf, max_depth=self.max_depth)
            
            # 自助采样
            indices = np.random.choice(len(X), len(X), replace=True)
            X_boot = X[indices]
            T_boot = T[indices]
            Y_boot = Y[indices]
            
            tree.fit(X_boot, T_boot, Y_boot)
            self.trees.append(tree)
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        预测
        
        Returns:
            (mean_effects, standard_errors)
        """
        effects = np.zeros(len(X))
        ses = np.zeros(len(X))
        
        predictions = []
        
        for tree in self.trees:
            pred, _ = tree.predict(X)
            predictions.append(pred)
        
        predictions = np.array(predictions)
        
        # 平均
        effects = predictions.mean(axis=0)
        
        # 标准误（树间变异）
        ses = predictions.std(axis=0) / np.sqrt(self.n_estimators)
        
        return effects, ses


class GRFWrapped:
    """
    GRF (Generalized Random Forests) 包装器
    
    简化实现
    """
    
    def __init__(self, n_estimators: int = 100):
        self.n_estimators = n_estimators
    
    def fit(self, X: np.ndarray, T: np.ndarray, Y: np.ndarray):
        """拟合"""
        self.causal_forest = CausalForest(n_estimators=self.n_estimators)
        self.causal_forest.fit(X, T, Y)
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """预测"""
        return self.causal_forest.predict(X)


def demo_causal_forest():
    """演示因果森林"""
    print("=== 因果森林演示 ===\n")
    
    np.random.seed(42)
    
    # 生成数据
    n = 1000
    
    # 协变量
    X1 = np.random.randn(n)
    X2 = np.random.randn(n)
    X = np.column_stack([X1, X2])
    
    # 异质性处理效应
    # tau(x) = 2 + 0.5 * X1
    tau = 2 + 0.5 * X1
    
    # 处理
    p_logit = X1 + X2
    p = 1 / (1 + np.exp(-p_logit))
    T = (np.random.rand(n) < p).astype(int)
    
    # 结果
    Y0 = np.random.randn(n)
    Y1 = tau + np.random.randn(n)
    Y = T * Y1 + (1 - T) * Y0
    
    print(f"样本量: {n}")
    print(f"处理组: {T.sum()}")
    print(f"异质性效应: τ(x) = 2 + 0.5 * X1")
    
    # 因果森林
    cf = CausalForest(n_estimators=50)
    cf.fit(X, T, Y)
    
    # 预测
    effects, ses = cf.predict(X)
    
    print(f"\n预测结果:")
    print(f"  效应均值: {effects.mean():.4f}")
    print(f"  效应标准误均值: {ses.mean():.4f}")
    
    # 按X1分组
    print("\n按X1分组的效应估计:")
    for x1_range in [(-2, -1), (-0.5, 0.5), (1, 2)]:
        mask = (X1 >= x1_range[0]) & (X1 <= x1_range[1])
        true_effect = 2 + 0.5 * (x1_range[0] + x1_range[1]) / 2
        print(f"  X1 in {x1_range}: 估计={effects[mask].mean():.4f}, 真值={true_effect:.4f}")


def demo_heterogeneous_effects():
    """演示异质性效应"""
    print("\n=== 异质性处理效应 ===\n")
    
    print("因果森林的优势:")
    print("  - 识别不同子群体的处理效应")
    print("  - 发现处理效应的异质性来源")
    print()
    
    print("应用场景:")
    print("  - 个性化医疗")
    print("  - 精准营销")
    print("  - 政策 Targeting")


def demo_confidence_intervals():
    """演示置信区间"""
    print("\n=== 置信区间 ===\n")
    
    print("因果森林提供两种不确定性:")
    print()
    
    print("1. 树内变异:")
    print("   - 每个叶子节点内的方差")
    print("   - 反映估计精度")
    print()
    
    print("2. 树间变异:")
    print("   - 不同树之间的差异")
    print("   - 反映模型不确定性")


if __name__ == "__main__":
    print("=" * 60)
    print("因果森林")
    print("=" * 60)
    
    # 因果森林演示
    demo_causal_forest()
    
    # 异质性效应
    demo_heterogeneous_effects()
    
    # 置信区间
    demo_confidence_intervals()
    
    print("\n" + "=" * 60)
    print("因果森林核心:")
    print("=" * 60)
    print("""
1. 因果树:
   - 使用诚实分裂
   - 目标是最小化处理效应异质性
   - 提供局部估计

2. 因果森林:
   - 多棵因果树的集成
   - 更稳定的估计
   - 更平滑的效应面

3. CATE估计:
   - τ(x) = E[Y(1) - Y(0) | X=x]
   - 异质性处理效应
   - 用于个性化决策

4. GRF:
   - Generalized Random Forests
   - 更一般的框架
   - R和Python实现可用
""")
