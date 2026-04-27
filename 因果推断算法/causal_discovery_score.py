# -*- coding: utf-8 -*-
"""
算法实现：因果推断算法 / causal_discovery_score

本文件实现 causal_discovery_score 相关的算法功能。
"""

import numpy as np
from typing import List, Dict, Set, Tuple, Optional
import math


class ScoreFunction:
    """评分函数基类"""
    
    def score(self, dag: Dict[str, Set[str]], data: Dict[str, np.ndarray]) -> float:
        """
        计算DAG的评分
        
        Args:
            dag: 有向无环图 {parent: {children}}
            data: 数据字典
        
        Returns:
            评分（越高越好）
        """
        raise NotImplementedError


class BDeuScore(ScoreFunction):
    """
    BDeu评分 (Bayesian Dirichlet equivalent uniform)
    
    BIC的特殊情况，等价样本大小(ESS)均匀分配
    """
    
    def __init__(self, ess: float = 1.0):
        """
        初始化
        
        Args:
            ess: 等价样本大小
        """
        self.ess = ess
    
    def score(self, dag: Dict[str, Set[str]], data: Dict[str, np.ndarray]) -> float:
        """
        计算BDeu评分
        
        Returns:
            局部评分之和
        """
        score_total = 0.0
        
        for node in dag:
            parents = {p for p, children in dag.items() if node in children}
            score_total += self._local_score(node, parents, data)
        
        return score_total
    
    def _local_score(self, node: str, parents: Set[str], 
                    data: Dict[str, np.ndarray]) -> float:
        """
        计算节点的局部评分
        
        Returns:
            BDeu(node | parents)
        """
        X = data[node]
        parent_data = {p: data[p] for p in parents}
        
        # 状态数
        x_states = len(np.unique(X))
        parent_configs = 1
        for p in parents:
            parent_configs *= len(np.unique(parent_data[p]))
        
        # 伪计数
        alpha = self.ess / parent_configs
        
        # BDeu公式（简化）
        n_ijk = len(X) * alpha / x_states / parent_configs
        alpha_ijk = alpha / x_states / parent_configs
        
        # 简化评分
        score = 0.0
        for i in range(x_states):
            for j in range(parent_configs):
                score += math.lgamma(alpha_ijk + n_ijk) - math.lgamma(alpha_ijk)
        
        return score


class BICScore(ScoreFunction):
    """
    BIC评分
    
    BIC = -2 * log-likelihood + k * log(n)
    """
    
    def __init__(self, penalty: float = 1.0):
        self.penalty = penalty
    
    def score(self, dag: Dict[str, Set[str]], data: Dict[str, np.ndarray]) -> float:
        """计算BIC评分"""
        score_total = 0.0
        
        for node in dag:
            parents = {p for p, children in dag.items() if node in children}
            score_total += self._local_score(node, parents, data)
        
        return score_total
    
    def _local_score(self, node: str, parents: Set[str],
                    data: Dict[str, np.ndarray]) -> float:
        """计算局部BIC评分"""
        X = data[node]
        n = len(X)
        
        if len(parents) == 0:
            # 无父节点：基于方差的评分
            var = np.var(X)
            if var < 1e-10:
                var = 1e-10
            score = -n * np.log(var) / 2
            score -= (1) * np.log(n) / 2
            return score
        
        # 有父节点：线性回归
        parent_names = list(parents)
        P = np.column_stack([data[p] for p in parent_names])
        
        try:
            # OLS
            beta = np.linalg.lstsq(P, X, rcond=None)[0]
            residuals = X - P @ beta
            rss = np.sum(residuals ** 2)
            sigma2 = rss / n
            
            # BIC
            k = len(parents) + 1
            score = -n * np.log(sigma2) / 2 - k * np.log(n) / 2
            
            return score
        except:
            return -float('inf')


class MDLScore(ScoreFunction):
    """
    MDL评分 (Minimum Description Length)
    
    MDL = 模型描述长度 + 数据描述长度
    """
    
    def score(self, dag: Dict[str, Set[str]], data: Dict[str, np.ndarray]) -> float:
        """计算MDL评分"""
        # 简化为BIC
        bic = BICScore()
        return bic.score(dag, data)


class ConditionalEntropyScore(ScoreFunction):
    """
    条件熵评分
    
    Score = -H(Y | Parents) + 复杂度惩罚
    """
    
    def score(self, dag: Dict[str, Set[str]], data: Dict[str, np.ndarray]) -> float:
        """计算评分"""
        score_total = 0.0
        
        for node in dag:
            parents = {p for p, children in dag.items() if node in children}
            score_total += self._local_score(node, parents, data)
        
        return score_total
    
    def _local_score(self, node: str, parents: Set[str],
                    data: Dict[str, np.ndarray]) -> float:
        """计算条件熵评分"""
        X = data[node]
        n = len(X)
        
        if len(parents) == 0:
            # 无父节点：熵
            _, counts = np.unique(X, return_counts=True)
            probs = counts / n
            entropy = -np.sum(probs * np.log(probs + 1e-10))
            return -entropy
        
        # 条件熵
        parent_data = {p: data[p] for p in parents}
        
        # 简化：使用线性条件熵
        return -np.var(X) * n


def demo_score_functions():
    """演示评分函数"""
    print("=== 因果发现评分函数演示 ===\n")
    
    np.random.seed(42)
    
    # 生成数据
    n = 100
    
    # X -> Z -> Y
    X = np.random.randn(n)
    Z = 0.5 * X + np.random.randn(n) * 0.1
    Y = 0.3 * Z + np.random.randn(n) * 0.1
    
    data = {'X': X, 'Y': Y, 'Z': Z}
    
    print("数据: X -> Z -> Y")
    
    # DAG
    dag1 = {  # 正确结构
        'X': set(),
        'Z': {'X'},
        'Y': {'Z'}
    }
    
    dag2 = {  # 错误结构
        'X': {'Z'},
        'Z': {'Y'},
        'Y': set()
    }
    
    dag3 = {  # 无关结构
        'X': set(),
        'Z': set(),
        'Y': set()
    }
    
    # BIC评分
    bic = BICScore()
    
    print("\nBIC评分:")
    score1 = bic.score(dag1, data)
    score2 = bic.score(dag2, data)
    score3 = bic.score(dag3, data)
    
    print(f"  正确结构 X->Z->Y: {score1:.2f}")
    print(f"  错误结构 Z->X, Y->Z: {score2:.2f}")
    print(f"  无边结构: {score3:.2f}")
    
    # BDeu评分
    bdeu = BDeuScore(ess=1.0)
    
    print("\nBDeu评分:")
    score1 = bdeu.score(dag1, data)
    score2 = bdeu.score(dag2, data)
    score3 = bdeu.score(dag3, data)
    
    print(f"  正确结构 X->Z->Y: {score1:.2f}")
    print(f"  错误结构 Z->X, Y->Z: {score2:.2f}")
    print(f"  无边结构: {score3:.2f}")


def demo_score_properties():
    """演示评分函数性质"""
    print("\n=== 评分函数性质 ===\n")
    
    print("评分函数应该满足:")
    print()
    
    print("1. 分解性:")
    print("   Score(G, D) = Σ_i Score(X_i | Pa(X_i), D)")
    print("   允许高效计算")
    
    print("\n2. 等价类等价:")
    print("   同一马尔可夫等价类应有相同评分")
    
    print("\n3. 忠实性:")
    print("   正确结构应该高分")


def demo_bdeu_vs_bic():
    """对比BDeu和BIC"""
    print("\n=== BDeu vs BIC ===\n")
    
    print("| 特性       | BDeu           | BIC            |")
    print("|-----------|----------------|----------------|")
    print("| 类型       | Bayesian       | 信息论         |")
    print("| 参数估计   | 贝叶斯估计     | 频率派          |")
    print("| 复杂度惩罚 | 自动          | 显式           |")
    print("| 适合       | 离散数据      | 连续数据        |")


if __name__ == "__main__":
    print("=" * 60)
    print("因果发现评分函数")
    print("=" * 60)
    
    # 评分演示
    demo_score_functions()
    
    # 性质
    demo_score_properties()
    
    # BDeu vs BIC
    demo_bdeu_vs_bic()
    
    print("\n" + "=" * 60)
    print("评分函数总结:")
    print("=" * 60)
    print("""
1. BDeu (Bayesian Dirichlet equivalent uniform):
   - 适合离散数据
   - 基于贝叶斯估计
   - ESS控制复杂度

2. BIC:
   - 适合连续数据
   - 渐近一致
   - 计算简单

3. MDL:
   - 基于信息论
   - 类似BIC
   - 最小描述长度

4. 选择建议:
   - 离散数据: BDeu
   - 连续数据: BIC/Gaussian
   - 混合数据: 混合方法
""")
