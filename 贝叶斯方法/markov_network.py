"""
马尔可夫网络（马尔可夫随机场）
Markov Networks (Markov Random Fields)

马尔可夫网络是无向图模型，与贝叶斯网络（有理图）相对。
使用因子分解描述联合分布。
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Callable
from collections import defaultdict


class Factor:
    """
    因子（势函数）
    
    参数:
        scope: 因子涉及的变量列表
        values: 势函数值数组
    """
    
    def __init__(self, scope: List[str], values: np.ndarray):
        self.scope = scope
        self.values = values
        self.var_to_dim = {var: i for i, var in enumerate(scope)}
    
    def get_value(self, assignment: Dict[str, int]) -> float:
        """获取给定赋值下的因子值"""
        indices = tuple(assignment.get(var, 0) for var in self.scope)
        return float(self.values[indices])
    
    def multiply(self, other: 'Factor') -> 'Factor':
        """因子相乘"""
        all_vars = list(set(self.scope) | set(other.scope))
        all_vars.sort()
        
        # 创建新的索引映射
        new_scope = all_vars
        new_values_shape = [2] * len(all_vars)  # 假设二元变量
        
        # 简化实现
        result = np.zeros(new_values_shape)
        for i in range(int(np.prod(new_values_shape))):
            indices = np.unravel_index(i, new_values_shape)
            assign = {var: indices[j] for j, var in enumerate(new_scope)}
            result[indices] = self.get_value(assign) * other.get_value(assign)
        
        return Factor(new_scope, result)
    
    def marginalize(self, var: str) -> 'Factor':
        """边际化"""
        if var not in self.scope:
            return Factor(self.scope.copy(), self.values.copy())
        
        dim = self.var_to_dim[var]
        new_scope = [v for v in self.scope if v != var]
        new_shape = [2] * len(new_scope)
        
        # 求和边际化
        result = np.sum(self.values, axis=dim)
        result = result.reshape(new_shape)
        
        return Factor(new_scope, result)
    
    def __repr__(self):
        return f"Factor(scope={self.scope}, shape={self.values.shape})"


class MarkovNetwork:
    """
    马尔可夫网络（马尔可夫随机场）
    
    联合分布分解为因子乘积：
    P(x) = (1/Z) * prod_{c} phi_c(x_c)
    
    参数:
        variables: 变量列表
        factors: 因子列表
    """
    
    def __init__(self, variables: List[str], factors: List[Factor]):
        self.variables = variables
        self.factors = factors
        self.n_vars = len(variables)
        
        # 构建邻接关系
        self.neighbors = defaultdict(set)
        for factor in factors:
            for var in factor.scope:
                for other in factor.scope:
                    if var != other:
                        self.neighbors[var].add(other)
    
    def partition_function(self) -> float:
        """
        计算配分函数 Z = sum_x prod_c phi_c(x_c)
        
        这是精确推断的难点，通常是NP难的
        """
        # 简化实现：枚举（仅适用于极小问题）
        n_states = 2  # 假设二元变量
        Z = 0.0
        
        for i in range(n_states ** self.n_vars):
            assignment = {var: (i // (n_states ** j)) % n_states 
                         for j, var in enumerate(self.variables)}
            
            # 计算因子乘积
            prob = 1.0
            for factor in self.factors:
                prob *= factor.get_value(assignment)
            
            Z += prob
        
        return Z
    
    def factor_product(self) -> Factor:
        """所有因子相乘"""
        if not self.factors:
            return Factor([], np.array([1.0]))
        
        result = self.factors[0]
        for factor in self.factors[1:]:
            result = result.multiply(factor)
        
        return result
    
    def unnormalized_prob(self, assignment: Dict[str, int]) -> float:
        """计算未归一化概率"""
        prob = 1.0
        for factor in self.factors:
            prob *= factor.get_value(assignment)
        return prob
    
    def gibbs_sampling(self, n_samples: int, burn_in: int = 100) -> List[Dict]:
        """
        Gibbs采样推断
        
        参数:
            n_samples: 样本数量
            burn_in: 燃烧期
            
        返回:
            样本列表
        """
        # 初始化
        assignment = {var: np.random.randint(2) for var in self.variables}
        samples = []
        
        for _ in range(burn_in + n_samples):
            # 依次更新每个变量
            for var in self.variables:
                # 计算条件分布 P(var | others)
                probs = [0.5, 0.5]  # 简化
                
                # 更新
                assignment[var] = np.random.choice(2, p=probs)
            
            if _ >= burn_in:
                samples.append(assignment.copy())
        
        return samples


class BeliefPropagationMRF:
    """
    马尔可夫网络上的置信传播（和-积算法）
    
    参数:
        mrf: 马尔可夫网络
    """
    
    def __init__(self, mrf: MarkovNetwork):
        self.mrf = mrf
        self.messages = {}  # (from, to) -> Factor
        self.beliefs = {}  # var -> Factor
    
    def run_loopy(self, n_iterations: int = 100) -> bool:
        """
        运行Loopy置信传播
        
        参数:
            n_iterations: 迭代次数
            
        返回:
            是否收敛
        """
        for iteration in range(n_iterations):
            old_messages = dict(self.messages)
            
            # 更新所有消息
            for var in self.mrf.variables:
                for neighbor in self.mrf.neighbors[var]:
                    self._compute_message(var, neighbor)
            
            # 检查收敛
            max_diff = 0
            for key in self.messages:
                if key in old_messages:
                    diff = np.max(np.abs(
                        self.messages[key].values - old_messages[key].values
                    ))
                    max_diff = max(max_diff, diff)
            
            if max_diff < 1e-6:
                return True
        
        return False
    
    def _compute_message(self, from_var: str, to_var: str):
        """计算从from_var到to_var的消息"""
        # 收集所有其他邻居传来的消息
        incoming = []
        for neighbor in self.mrf.neighbors[from_var]:
            if neighbor != to_var and (neighbor, from_var) in self.messages:
                incoming.append(self.messages[(neighbor, from_var)])
        
        # 获取涉及这两个变量的因子
        relevant_factors = []
        for factor in self.mrf.factors:
            if from_var in factor.scope and to_var in factor.scope:
                relevant_factors.append(factor)
        
        # 消息计算
        result_scope = [to_var]
        result_shape = [2]
        result_values = np.ones(result_shape)
        
        # 乘以相关因子
        for factor in relevant_factors:
            result_values = result_values * factor.values.flatten()
        
        # 乘以传入消息
        for msg in incoming:
            result_values = result_values * msg.values.flatten()
        
        # 归一化
        result_values = result_values / (np.sum(result_values) + 1e-10)
        
        self.messages[(from_var, to_var)] = Factor(result_scope, result_values)
    
    def compute_beliefs(self):
        """计算所有变量的边缘信念"""
        for var in self.mrf.variables:
            # 收集所有传入消息
            belief_factors = []
            
            for neighbor in self.mrf.neighbors[var]:
                if (neighbor, var) in self.messages:
                    belief_factors.append(self.messages[(neighbor, var)])
            
            # 乘积并归一化
            if belief_factors:
                belief = belief_factors[0]
                for bf in belief_factors[1:]:
                    belief = belief.multiply(bf)
            else:
                belief = Factor([var], np.array([0.5, 0.5]))
            
            self.beliefs[var] = belief
    
    def query(self, var: str) -> Dict[int, float]:
        """
        查询边缘概率
        
        参数:
            var: 查询变量
            
        返回:
            边缘概率分布
        """
        if not self.beliefs:
            self.compute_beliefs()
        
        belief = self.beliefs.get(var)
        if belief is None:
            return {0: 0.5, 1: 0.5}
        
        probs = belief.values.flatten()
        return {i: float(p) for i, p in enumerate(probs)}


class IsingModel(MarkovNetwork):
    """
    Ising模型（马尔可夫网络的经典例子）
    
    用于建模二元变量的相互作用
    P(x) = (1/Z) * exp(sum_{i<j} J_ij * x_i * x_j + sum_i h_i * x_i)
    """
    
    def __init__(self, variables: List[str], J: Dict[Tuple[str, str], float],
                 h: Dict[str, float]):
        """
        参数:
            variables: 变量列表
            J: 相互作用强度 {(i,j): J_ij}
            h: 外部场 {i: h_i}
        """
        self.variables = variables
        self.J = J
        self.h = h
        
        # 创建因子
        factors = []
        
        # 成对因子
        for (i, j), J_ij in J.items():
            scope = [i, j]
            values = np.array([
                [np.exp(J_ij), np.exp(-J_ij)],
                [np.exp(-J_ij), np.exp(J_ij)]
            ])
            factors.append(Factor(scope, values))
        
        # 单点因子
        for i, h_i in h.items():
            scope = [i]
            values = np.array([np.exp(h_i), np.exp(-h_i)])
            factors.append(Factor(scope, values))
        
        super().__init__(variables, factors)


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("马尔可夫网络测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 测试1：简单马尔可夫网络
    print("\n1. 简单马尔可夫网络:")
    
    variables = ['A', 'B', 'C']
    
    # 创建因子
    # phi(A, B)
    phi_AB = Factor(['A', 'B'], np.array([[1.0, 0.5], [0.5, 1.0]]))
    # phi(B, C)
    phi_BC = Factor(['B', 'C'], np.array([[1.0, 0.5], [0.5, 1.0]]))
    
    mrf = MarkovNetwork(variables, [phi_AB, phi_BC])
    
    print(f"   变量: {mrf.variables}")
    print(f"   因子数: {len(mrf.factors)}")
    print(f"   A的邻居: {mrf.neighbors['A']}")
    print(f"   B的邻居: {mrf.neighbors['B']}")
    
    # 计算未归一化概率
    assignment = {'A': 0, 'B': 1, 'C': 0}
    prob = mrf.unnormalized_prob(assignment)
    print(f"   P(A=0,B=1,C=0) ∝ {prob:.4f}")
    
    # 测试2：Ising模型
    print("\n2. Ising模型:")
    
    variables = ['S1', 'S2', 'S3']
    J = {
        ('S1', 'S2'): 1.0,
        ('S2', 'S3'): -0.5,
    }
    h = {'S1': 0.5, 'S2': 0.0, 'S3': -0.5}
    
    ising = IsingModel(variables, J, h)
    
    print(f"   变量: {ising.variables}")
    print(f"   相互作用: {ising.J}")
    print(f"   外部场: {ising.h}")
    
    # 计算配分函数（近似）
    print(f"   因子数: {len(ising.factors)}")
    
    # 测试3：Gibbs采样
    print("\n3. Gibbs采样:")
    
    variables = ['X', 'Y', 'Z']
    
    # 创建简单因子
    phi_XY = Factor(['X', 'Y'], np.array([[2.0, 1.0], [1.0, 2.0]]))
    phi_YZ = Factor(['Y', 'Z'], np.array([[2.0, 1.0], [1.0, 2.0]]))
    
    mrf_simple = MarkovNetwork(variables, [phi_XY, phi_YZ])
    samples = mrf_simple.gibbs_sampling(n_samples=100, burn_in=50)
    
    print(f"   采样数: {len(samples)}")
    
    # 统计频率
    x_ones = sum(s['X'] for s in samples) / len(samples)
    y_ones = sum(s['Y'] for s in samples) / len(samples)
    z_ones = sum(s['Z'] for s in samples) / len(samples)
    
    print(f"   X=1频率: {x_ones:.3f}")
    print(f"   Y=1频率: {y_ones:.3f}")
    print(f"   Z=1频率: {z_ones:.3f}")
    
    # 测试4：Loopy置信传播
    print("\n4. Loopy置信传播:")
    
    bp = BeliefPropagationMRF(mrf_simple)
    converged = bp.run_loopy(n_iterations=20)
    
    print(f"   收敛: {converged}")
    
    bp.compute_beliefs()
    
    for var in variables:
        probs = bp.query(var)
        print(f"   P({var}=1) = {probs[1]:.4f}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
