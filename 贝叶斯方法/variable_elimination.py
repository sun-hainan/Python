"""
变量消除算法(Variable Elimination)实现
Variable Elimination Algorithm Implementation

变量消除是贝叶斯网络精确推理的核心算法。
通过选择合适的变量消除顺序，逐步边际化因子来计算边缘概率。
"""

import numpy as np
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Set


class Factor:
    """
    因子类，表示变量子集上的联合势函数
    
    属性:
        scope: 涉及的变量列表
        values: 多维数组，存储势函数值
    """
    
    def __init__(self, scope: List[str], values: np.ndarray):
        self.scope = scope  # 变量列表
        self.values = values  # 势函数值
        self._build_index()
    
    def _build_index(self):
        """建立变量名到维度的映射"""
        self.var_to_dim = {var: i for i, var in enumerate(self.scope)}
    
    def get_value(self, assignment: Dict[str, int]) -> float:
        """
        根据变量赋值获取因子值
        
        参数:
            assignment: 变量赋值字典
            
        返回:
            对应的势函数值
        """
        # 构建索引
        indices = tuple(assignment[var] for var in self.scope)
        return float(self.values[indices])
    
    def marginalize(self, var: str) -> 'Factor':
        """
        边际化：消除变量var，对其他变量求和
        
        参数:
            var: 要消除的变量
            
        返回:
            新的边际化后的因子
        """
        if var not in self.var_to_dim:
            return Factor(self.scope.copy(), self.values.copy())
        
        dim = self.var_to_dim[var]
        new_scope = [v for v in self.scope if v != var]
        
        # 计算边际化：沿着dim维度求和
        new_values = np.sum(self.values, axis=dim)
        
        return Factor(new_scope, new_values)
    
    def multiply(self, other: 'Factor') -> 'Factor':
        """
        因子相乘：将两个因子的势函数相乘
        
        参数:
            other: 另一个因子
            
        返回:
            乘积因子
        """
        # 合并变量列表
        all_vars = list(set(self.scope) | set(other.scope))
        all_vars.sort(key=lambda v: self.var_to_dim.get(v, other.var_to_dim.get(v, 0)))
        
        # 计算需要的维度顺序
        self_axes = [all_vars.index(v) for v in self.scope]
        other_axes = [all_vars.index(v) for v in other.scope]
        
        # 使用einsum进行高效乘法
        result_values = np.einsum(
            self.values, self_axes,
            other.values, other_axes,
            all_vars
        )
        
        return Factor(all_vars, result_values)
    
    def reduce(self, var: str, value: int) -> 'Factor':
        """
        条件化：将变量var设置为特定值
        
        参数:
            var: 变量名
            value: 要设置的值(0或1)
            
        返回:
            条件化后的因子
        """
        if var not in self.var_to_dim:
            return Factor(self.scope.copy(), self.values.copy())
        
        dim = self.var_to_dim[var]
        new_scope = [v for v in self.scope if v != var]
        
        # 沿着该维度切片
        slices = [slice(None)] * len(self.scope)
        slices[dim] = value
        new_values = self.values[tuple(slices)]
        
        # 调整维度顺序
        new_values = np.transpose(new_values, 
                                   [i for i in range(len(self.scope)) if i != dim])
        
        return Factor(new_scope, new_values)


class VariableElimination:
    """
    变量消除算法实现
    
    支持：
    - 自定义变量消除顺序
    - 自动选择最优顺序（启发式）
    - 证据条件化
    """
    
    def __init__(self, network: 'BayesianNetwork'):
        self.network = network  # 贝叶斯网络引用
        self.factors = {}  # 每个变量的因子
    
    def get_factors_for_variable(self, var: str) -> List[Factor]:
        """获取涉及某变量的所有因子"""
        factors = []
        
        # CPT因子
        if var in self.network.cpts:
            scope = self.network.parents[var] + [var]
            values = np.array(self.network.cpts[var])
            factors.append(Factor(scope, values))
        
        # 如果是父节点，其CPT也是其他因子的组成部分
        for child in self.network.children[var]:
            if child in self.network.cpts:
                scope = self.network.parents[child] + [child]
                values = np.array(self.network.cpts[child])
                factors.append(Factor(scope, values))
        
        return factors
    
    def min_degree_order(self, query_var: str, evidence: Set[str]) -> List[str]:
        """
        最小度启发式(Min-Degree Heuristic)选择消除顺序
        
        参数:
            query_var: 查询变量
            evidence: 证据变量集合
            
        返回:
            消除顺序列表
        """
        # 构建约束图
        remaining = set(self.network.variables) - {query_var} - evidence
        
        order = []
        current_remaining = set(remaining)
        
        while current_remaining:
            min_degree = float('inf')
            min_var = None
            
            for var in current_remaining:
                # 计算该变量的度（邻居数量）
                neighbors = set()
                
                # 获取该变量的因子
                for f_scope in [self.network.parents.get(var, []) + [var]]:
                    neighbors.update(f_scope)
                
                neighbors = neighbors - {var} - evidence - {query_var}
                degree = len(neighbors)
                
                if degree < min_degree:
                    min_degree = degree
                    min_var = var
            
            if min_var:
                order.append(min_var)
                current_remaining.remove(min_var)
            else:
                # 如果没有变量可选，选择任意一个
                min_var = list(current_remaining)[0]
                order.append(min_var)
                current_remaining.remove(min_var)
        
        return order
    
    def eliminate(self, var: str, factors: List[Factor]) -> Tuple[Factor, List[Factor]]:
        """
        消除单个变量：将所有涉及该变量的因子相乘，然后边际化
        
        参数:
            var: 要消除的变量
            factors: 当前因子列表
            
        返回:
            (消除后的因子, 更新后的因子列表)
        """
        # 收集涉及该变量的因子
        involved = []
        remaining = []
        
        for f in factors:
            if var in f.scope:
                involved.append(f)
            else:
                remaining.append(f)
        
        if not involved:
            return Factor([], np.array(1.0)), remaining
        
        # 相乘所有涉及该变量的因子
        product = involved[0]
        for f in involved[1:]:
            product = product.multiply(f)
        
        # 边际化消除该变量
        result = product.marginalize(var)
        
        return result, remaining + [result]
    
    def query(self, query_var: str, evidence: Optional[Dict[str, int]] = None,
              elimination_order: Optional[List[str]] = None) -> Dict[int, float]:
        """
        执行查询：计算边缘概率 P(query_var | evidence)
        
        参数:
            query_var: 查询变量名
            evidence: 证据变量字典 {变量名: 值}
            elimination_order: 消除顺序（可选）
            
        返回:
            查询变量的边缘概率分布 {值: 概率}
        """
        evidence = evidence or {}
        evidence_set = set(evidence.keys())
        
        # 初始化因子
        factors = []
        
        for var in self.network.variables:
            scope = self.network.parents[var] + [var]
            values = np.array(self.network.cpts[var])
            
            # 如果有证据，对该变量进行条件化
            if var in evidence:
                f = Factor(scope, values)
                f = f.reduce(var, evidence[var])
                factors.append(f)
            else:
                factors.append(Factor(scope, values))
        
        # 选择消除顺序
        if elimination_order is None:
            elimination_order = self.min_degree_order(query_var, evidence_set)
        
        # 依次消除变量
        for var in elimination_order:
            if var == query_var or var in evidence_set:
                continue
            
            _, factors = self.eliminate(var, factors)
        
        # 合并剩余因子
        result = factors[0]
        for f in factors[1:]:
            result = result.multiply(f)
        
        # 归一化
        probs = result.values.flatten()
        total = np.sum(probs)
        if total > 0:
            probs = probs / total
        
        return {i: float(p) for i, p in enumerate(probs)}


class BayesianNetwork:
    """简化的贝叶斯网络类"""
    
    def __init__(self):
        self.variables = []
        self.parents = defaultdict(list)
        self.children = defaultdict(list)
        self.cpts = {}
    
    @classmethod
    def from_struc(cls, variables: List[str], edges: List[Tuple[str, str]], 
                   cpts: Dict[str, np.ndarray]) -> 'BayesianNetwork':
        """从结构创建网络"""
        bn = cls()
        bn.variables = variables
        bn.cpts = cpts
        
        for parent, child in edges:
            bn.parents[child].append(parent)
            bn.children[parent].append(child)
        
        return bn


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("变量消除算法测试")
    print("=" * 60)
    
    # 创建简单的贝叶斯网络
    # 示例：天气决定是否带伞
    # 变量：C=Cloudy(云), R=Rain(雨), S=Sprinkler(洒水器), W=Wet(地面湿)
    # 拓扑：C -> R, C -> S, R -> W, S -> W
    
    variables = ['C', 'R', 'S', 'W']
    edges = [('C', 'R'), ('C', 'S'), ('R', 'W'), ('S', 'W')]
    
    # 条件概率表
    # P(C)
    p_C = [0.5, 0.5]  # P(C=0)=0.5, P(C=1)=0.5
    # P(R|C)
    p_R_given_C = [
        [0.8, 0.2],  # R=0 given C
        [0.2, 0.8],  # R=1 given C
    ]
    # P(S|C)
    p_S_given_C = [
        [0.5, 0.5],  # S=0 given C
        [0.9, 0.1],  # S=1 given C
    ]
    # P(W|R,S)
    p_W_given_R_S = [
        # W=0
        [[0.99, 0.60], [0.90, 0.01]],  # given R,S
        # W=1
        [[0.01, 0.40], [0.10, 0.99]],  # given R,S
    ]
    
    cpts = {
        'C': p_C,
        'R': p_R_given_C,
        'S': p_S_given_C,
        'W': p_W_given_R_S,
    }
    
    bn = BayesianNetwork.from_struc(variables, edges, cpts)
    ve = VariableElimination(bn)
    
    print("\n1. 查询 P(W=1 | C=1)")
    result = ve.query('W', evidence={'C': 1})
    print(f"   P(W=0 | C=1) = {result[0]:.4f}")
    print(f"   P(W=1 | C=1) = {result[1]:.4f}")
    
    print("\n2. 查询 P(R | W=1)")
    result = ve.query('R', evidence={'W': 1})
    print(f"   P(R=0 | W=1) = {result[0]:.4f}")
    print(f"   P(R=1 | W=1) = {result[1]:.4f}")
    
    print("\n3. 查询 P(C | W=1)")
    result = ve.query('C', evidence={'W': 1})
    print(f"   P(C=0 | W=1) = {result[0]:.4f}")
    print(f"   P(C=1 | W=1) = {result[1]:.4f}")
    
    print("\n4. 查询 P(W=1 | R=1, S=1)")
    result = ve.query('W', evidence={'R': 1, 'S': 1})
    print(f"   P(W=0 | R=1, S=1) = {result[0]:.4f}")
    print(f"   P(W=1 | R=1, S=1) = {result[1]:.4f}")
    
    print("\n5. 消除顺序选择测试")
    order = ve.min_degree_order('W', set())
    print(f"   最小度启发式顺序: {order}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
