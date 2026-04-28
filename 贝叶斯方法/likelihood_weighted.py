"""
似然加权采样（Likelihood Weighting）用于贝叶斯网络
Likelihood Weighting Sampling for Bayesian Networks

似然加权是一种重要采样（Importance Sampling）变体，
专门用于带证据变量的贝叶斯网络推理。
通过固定证据变量，只对非证据变量采样来减少方差。
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Callable
from collections import defaultdict


class BayesianNetwork:
    """简化的贝叶斯网络"""
    
    def __init__(self, variables: List[str], edges: List[Tuple[str, str]], 
                 cpts: Dict[str, np.ndarray], parents: Dict[str, List[str]]):
        self.variables = variables
        self.edges = edges
        self.cpts = cpts
        self.parents = parents
        
        # 拓扑排序
        self.topo_order = self._topological_sort()
    
    def _topological_sort(self) -> List[str]:
        """拓扑排序"""
        in_degree = defaultdict(int)
        for parent, child in self.edges:
            in_degree[child] += 1
        
        queue = [v for v in self.variables if in_degree[v] == 0]
        order = []
        
        while queue:
            node = queue.pop(0)
            order.append(node)
            for parent, child in self.edges:
                if parent == node:
                    in_degree[child] -= 1
                    if in_degree[child] == 0:
                        queue.append(child)
        
        return order


class LikelihoodWeighting:
    """
    似然加权采样算法
    
    核心思想：
    1. 证据变量固定为观测值
    2. 非证据变量从条件分布采样
    3. 每个样本带有权重，反映该样本与证据的吻合程度
    
    参数:
        bn: 贝叶斯网络
        evidence: 证据变量字典
        n_samples: 采样数量
    """
    
    def __init__(self, bn: BayesianNetwork, evidence: Dict[str, int], 
                 n_samples: int = 1000):
        self.bn = bn
        self.evidence = evidence
        self.n_samples = n_samples
        
        self.samples = []
        self.weights = []
    
    def sample(self) -> Tuple[Dict[str, int], float]:
        """
        采样一个加权样本
        
        返回:
            (样本字典, 权重)
        """
        sample = {}
        weight = 1.0
        
        for var in self.bn.topo_order:
            if var in self.evidence:
                # 证据变量：固定为观测值
                sample[var] = self.evidence[var]
                
                # 更新权重：乘以 P(证据值 | 父节点值)
                parent_vals = [sample[p] for p in self.bn.parents[var]]
                cpt = self.bn.cpts[var]
                
                if not self.bn.parents[var]:
                    # 无父节点，直接取概率
                    p_evidence = cpt[self.evidence[var]]
                else:
                    # 按父节点取值索引
                    if len(parent_vals) == 1:
                        p_evidence = cpt[parent_vals[0]][self.evidence[var]]
                    elif len(parent_vals) == 2:
                        p_evidence = cpt[parent_vals[0]][parent_vals[1]][self.evidence[var]]
                    else:
                        # 更复杂的CPT
                        idx = tuple(parent_vals + [self.evidence[var]])
                        p_evidence = cpt[idx]
                
                weight *= p_evidence
            else:
                # 非证据变量：从条件分布采样
                parent_vals = [sample[p] for p in self.bn.parents[var]]
                cpt = self.bn.cpts[var]
                
                # 获取条件概率分布
                if not self.bn.parents[var]:
                    probs = cpt
                elif len(parent_vals) == 1:
                    probs = cpt[parent_vals[0]]
                elif len(parent_vals) == 2:
                    probs = cpt[parent_vals[0]][parent_vals[1]]
                else:
                    idx = tuple(parent_vals)
                    probs = cpt[idx]
                
                # 采样
                probs = np.array(probs) / np.sum(probs)
                sample[var] = np.random.choice(len(probs), p=probs)
        
        return sample, weight
    
    def run(self) -> Tuple[List[Dict], np.ndarray]:
        """
        运行似然加权采样
        
        返回:
            (样本列表, 权重数组)
        """
        self.samples = []
        self.weights = []
        
        for _ in range(self.n_samples):
            s, w = self.sample()
            self.samples.append(s)
            self.weights.append(w)
        
        self.weights = np.array(self.weights)
        
        # 归一化权重
        total = np.sum(self.weights)
        if total > 0:
            self.weights = self.weights / total
        
        return self.samples, self.weights
    
    def query(self, query_var: str) -> Dict[int, float]:
        """
        查询边缘概率
        
        参数:
            query_var: 查询变量
            
        返回:
            边缘概率分布 {值: 概率}
        """
        if not self.weights.any():
            self.run()
        
        # 加权直方图
        counts = defaultdict(float)
        
        for sample, weight in zip(self.samples, self.weights):
            val = sample[query_var]
            counts[val] += weight
        
        # 归一化
        total = sum(counts.values())
        if total > 0:
            counts = {k: v / total for k, v in counts.items()}
        
        return dict(counts)
    
    def conditional_query(self, query_var: str, given_var: str) -> Dict[int, Dict[int, float]]:
        """
        条件查询 P(query | given)
        
        参数:
            query_var: 查询变量
            given_var: 条件变量
            
        返回:
            条件概率字典 {given值: {query值: 概率}}
        """
        if not self.weights.any():
            self.run()
        
        # 收集联合计数
        joint_counts = defaultdict(lambda: defaultdict(float))
        given_counts = defaultdict(float)
        
        for sample, weight in zip(self.samples, self.weights):
            given_val = sample[given_var]
            query_val = sample[query_var]
            
            joint_counts[given_val][query_val] += weight
            given_counts[given_val] += weight
        
        # 归一化得到条件概率
        result = {}
        for given_val in joint_counts:
            result[given_val] = {}
            for query_val in joint_counts[given_val]:
                if given_counts[given_val] > 0:
                    result[given_val][query_val] = (
                        joint_counts[given_val][query_val] / given_counts[given_val]
                    )
        
        return result


class WeightedSample:
    """加权样本容器"""
    
    def __init__(self, sample: Dict[str, int], weight: float):
        self.sample = sample
        self.weight = weight
    
    def __repr__(self):
        return f"WeightedSample(sample={self.sample}, weight={self.weight:.4f})"


class AdaptiveLikelihoodWeighting:
    """
    自适应似然加权采样
    
    根据采样过程中的方差自动调整采样数量。
    
    参数:
        bn: 贝叶斯网络
        evidence: 证据变量
        target_variance: 目标方差
        initial_samples: 初始采样数
    """
    
    def __init__(self, bn: BayesianNetwork, evidence: Dict[str, int],
                 target_variance: float = 0.01, initial_samples: int = 100):
        self.bn = bn
        self.evidence = evidence
        self.target_variance = target_variance
        self.initial_samples = initial_samples
    
    def run(self) -> Tuple[List[Dict], np.ndarray]:
        """运行自适应采样"""
        lw = LikelihoodWeighting(self.bn, self.evidence, self.initial_samples)
        samples, weights = lw.run()
        
        # 检查方差
        current_var = np.var(weights) / (np.mean(weights)**2 + 1e-10)
        
        extra_samples = 0
        while current_var > self.target_variance and extra_samples < 5000:
            # 继续采样
            s, w = lw.sample()
            samples.append(s)
            weights = np.append(weights, w)
            extra_samples += 1
            
            current_var = np.var(weights) / (np.mean(weights)**2 + 1e-10)
        
        # 归一化
        weights = weights / np.sum(weights)
        
        return samples, weights


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("似然加权采样测试")
    print("=" * 60)
    
    # 构建测试网络：简单串联 A -> B -> C
    print("\n1. 简单串联网络测试:")
    
    variables = ['A', 'B', 'C']
    edges = [('A', 'B'), ('B', 'C')]
    parents = {'A': [], 'B': ['A'], 'C': ['B']}
    
    cpts = {
        'A': [0.6, 0.4],  # P(A)
        'B': [  # P(B|A)
            [0.7, 0.2],  # B=0 given A
            [0.3, 0.8],  # B=1 given A
        ],
        'C': [  # P(C|B)
            [0.8, 0.1],  # C=0 given B
            [0.2, 0.9],  # C=1 given B
        ],
    }
    
    bn = BayesianNetwork(variables, edges, cpts, parents)
    
    # 查询 P(A | C=1)
    print("   查询 P(A | C=1)")
    lw = LikelihoodWeighting(bn, evidence={'C': 1}, n_samples=5000)
    samples, weights = lw.run()
    
    result = lw.query('A')
    print(f"   P(A=0 | C=1) = {result.get(0, 0):.4f}")
    print(f"   P(A=1 | C=1) = {result.get(1, 0):.4f}")
    
    # 理论值（通过枚举验证）
    p_c1 = (0.6 * 0.3 * 0.9 + 0.4 * 0.8 * 0.9)  # 近似值
    p_a1_c1 = (0.4 * 0.8 * 0.9) / p_c1  # P(A=1|C=1)
    print(f"   理论参考 P(A=1|C=1) ≈ {p_a1_c1:.4f}")
    
    # 测试条件查询
    print("\n2. 条件查询 P(B | A):")
    lw2 = LikelihoodWeighting(bn, evidence={}, n_samples=1000)
    lw2.run()
    
    cond_result = lw2.conditional_query('B', 'A')
    print(f"   P(B=1 | A=0) = {cond_result[0].get(1, 0):.4f}")
    print(f"   P(B=1 | A=1) = {cond_result[1].get(1, 0):.4f}")
    print(f"   理论值: P(B=1|A=0)=0.2, P(B=1|A=1)=0.8")
    
    # 测试复杂网络
    print("\n3. 更大网络测试:")
    
    # 构建 Alarm 网络简化版
    # B(Burglary) -> A(Alarm) <- E(Earthquake)
    # A -> J(John)
    
    variables2 = ['B', 'E', 'A', 'J']
    edges2 = [('B', 'A'), ('E', 'A'), ('A', 'J')]
    parents2 = {'B': [], 'E': [], 'A': ['B', 'E'], 'J': ['A']}
    
    cpts2 = {
        'B': [0.99, 0.01],  # P(B)
        'E': [0.98, 0.02],  # P(E)
        'A': [  # P(A|B,E)
            [[0.999, 0.06], [0.71, 0.05]],  # A=0
            [[0.001, 0.94], [0.29, 0.95]],  # A=1
        ],
        'J': [  # P(J|A)
            [0.95, 0.10],  # J=0
            [0.05, 0.90],  # J=1
        ],
    }
    
    bn2 = BayesianNetwork(variables2, edges2, cpts2, parents2)
    
    print("   查询 P(B | J=1)")
    lw3 = LikelihoodWeighting(bn2, evidence={'J': 1}, n_samples=10000)
    lw3.run()
    result3 = lw3.query('B')
    print(f"   P(B=0 | J=1) = {result3.get(0, 0):.4f}")
    print(f"   P(B=1 | J=1) = {result3.get(1, 0):.4f}")
    
    # 加权样本统计
    print("\n4. 加权样本统计:")
    print(f"   有效样本数: {1 / np.sum(lw3.weights**2):.1f}")
    print(f"   权重方差: {np.var(lw3.weights):.8f}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
