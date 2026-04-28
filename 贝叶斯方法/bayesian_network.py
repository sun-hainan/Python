"""
贝叶斯网络实现：信念传播与变量消除
Bayesian Network: Belief Propagation and Variable Elimination

贝叶斯网络是有向无环图(DAG)，节点表示随机变量，边表示条件依赖关系。
本实现支持：构造网络、变量消除法推理、信念传播法推理。
"""

import numpy as np
from collections import defaultdict
from typing import Dict, List, Tuple, Optional


class BayesianNetwork:
    """
    贝叶斯网络类
    
    参数:
        variables: 变量名列表
        edges: 边列表，每个元素为(parent, child)元组
        cpts: 条件概率表字典，key为变量名，value为CPT矩阵
    """
    
    def __init__(self, variables: List[str], edges: List[Tuple[str, str]], cpts: Dict[str, np.ndarray]):
        self.variables = variables  # 所有变量
        self.edges = edges  # 有向边 (父节点, 子节点)
        self.cpts = cpts  # 条件概率表
        
        # 构建父节点字典
        self.parents = defaultdict(list)
        for parent, child in edges:
            self.parents[child].append(parent)
        
        # 构建子节点字典
        self.children = defaultdict(list)
        for parent, child in edges:
            self.children[parent].append(child)
    
    def topological_order(self) -> List[str]:
        """
        计算拓扑排序
        
        返回:
            变量的拓扑排序列表
        """
        in_degree = defaultdict(int)
        for parent, child in self.edges:
            in_degree[child] += 1
        
        queue = [v for v in self.variables if in_degree[v] == 0]
        order = []
        
        while queue:
            node = queue.pop(0)
            order.append(node)
            for child in self.children[node]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)
        
        return order


class Factor:
    """
    因子(Factor)类，用于变量消除算法
    
    属性:
        scope: 因子涉及的变量列表
        vars_index: 变量到索引的映射
        values: 因子值数组
    """
    
    def __init__(self, scope: List[str], values: np.ndarray):
        self.scope = scope  # 因子涉及的变量
        self.values = values  # 因子值数组
        self.vars_index = {var: i for i, var in enumerate(scope)}
    
    def marginalize(self, var: str) -> 'Factor':
        """
        对因子进行边际化，消除变量var
        
        参数:
            var: 要消除的变量名
            
        返回:
            边际化后的新因子
        """
        if var not in self.vars_index:
            return self
        
        var_idx = self.vars_index[var]
        new_scope = [v for v in self.scope if v != var]
        
        # 对var维度求和
        axis_to_sum = len(self.scope) - 1 - list(reversed(self.scope)).index(var)
        new_values = np.sum(self.values, axis=axis_to_sum)
        
        # 调整维度顺序
        remaining_vars = [v for v in self.scope if v != var]
        new_factor = Factor(remaining_vars, new_values)
        
        return new_factor
    
    def multiply(self, other: 'Factor') -> 'Factor':
        """
        两个因子相乘
        
        参数:
            other: 另一个因子
            
        返回:
            乘积因子
        """
        # 合并变量
        all_vars = list(set(self.scope + other.scope))
        all_vars.sort(key=lambda v: self.vars_index.get(v, other.vars_index.get(v, 0)))
        
        # 计算新形状
        shape = [2] * len(all_vars)  # 假设二元变量
        
        # 计算各自的索引
        self_axes = [all_vars.index(v) for v in self.scope]
        other_axes = [all_vars.index(v) for v in other.scope]
        
        # 使用np.einsum进行因子相乘
        result = np.einsum(self.values, self_axes, [other.vars_index], other_axes, all_vars)
        
        return Factor(all_vars, result)


def variable_elimination(bn: BayesianNetwork, query_var: str, 
                         evidence: Dict[str, int]) -> Dict[int, float]:
    """
    变量消除算法(Variable Elimination)
    
    参数:
        bn: 贝叶斯网络
        query_var: 查询变量名
        evidence: 证据变量字典 {变量名: 观测值}
        
    返回:
        查询变量的边缘概率分布字典 {值: 概率}
    """
    # 获取拓扑序
    order = bn.topological_order()
    
    # 初始化因子列表
    factors = []
    
    # 为每个节点创建因子
    for var in bn.variables:
        parents = bn.parents[var]
        scope = parents + [var]
        
        cpt = bn.cpts[var]
        
        # 如果有证据，调整因子
        if var in evidence:
            # 将该变量边缘化为证据值
            evidence_idx = evidence[var]
            if len(scope) == 1:
                factor_values = np.array([1.0, 1.0])
                factor_values[evidence_idx] = cpt[evidence_idx] if len(cpt) > evidence_idx else 1.0
            else:
                # 假设cpt的最后一维是子节点
                axis = len(scope) - 1
                mask = list(range(cpt.shape[-1]))
                new_cpt = np.zeros_like(cpt)
                for idx in range(cpt.shape[-1]):
                    if idx == evidence_idx:
                        new_cpt[..., idx] = cpt[..., idx]
                factor_values = new_cpt
        else:
            factor_values = cpt
        
        factors.append(Factor(scope, np.array(factor_values)))
    
    # 变量消除过程
    for var in order:
        # 如果是查询变量或证据变量，跳过
        if var == query_var or var in evidence:
            continue
        
        # 收集涉及该变量的所有因子
        var_factors = []
        remaining_factors = []
        
        for f in factors:
            if var in f.scope:
                var_factors.append(f)
            else:
                remaining_factors.append(f)
        
        # 相乘所有涉及该变量的因子
        if var_factors:
            result_factor = var_factors[0]
            for f in var_factors[1:]:
                result_factor = result_factor.multiply(f)
            
            # 边际化消除该变量
            result_factor = result_factor.marginalize(var)
            
            remaining_factors.append(result_factor)
        
        factors = remaining_factors
    
    # 合并所有剩余因子
    final_factor = factors[0]
    for f in factors[1:]:
        final_factor = final_factor.multiply(f)
    
    # 归一化得到边缘概率
    prob_values = final_factor.values
    if prob_values.ndim > 1:
        prob_values = np.sum(prob_values, axis=tuple(range(prob_values.ndim - 1)))
    
    total = np.sum(prob_values)
    if total > 0:
        prob_values = prob_values / total
    
    return {i: float(p) for i, p in enumerate(prob_values.flatten())}


def belief_propagation(bn: BayesianNetwork, query_var: str, 
                       evidence: Dict[str, int], max_iter: int = 100) -> Dict[int, float]:
    """
    信念传播算法(Belief Propagation) - 适用于树结构
    
    参数:
        bn: 贝叶斯网络
        query_var: 查询变量
        evidence: 证据变量
        max_iter: 最大迭代次数
        
    返回:
        查询变量的边缘概率
    """
    # 初始化消息
    messages = {}  # (from, to) -> Factor
    
    # 构建邻接表
    adj = defaultdict(list)
    for parent, child in bn.edges:
        adj[parent].append(child)
        adj[child].append(parent)
    
    def send_message(node: str, parent: str) -> Factor:
        """
        从node向parent发送消息
        """
        # 收集所有子节点的消息（除了parent）
        incoming = []
        for child in bn.children[node]:
            if child in evidence:
                continue
            if (child, node) in messages:
                incoming.append(messages[(child, node)])
        
        # 获取节点的CPT/先验
        if bn.parents[node]:
            scope = bn.parents[node] + [node]
        else:
            scope = [node]
        
        cpt = bn.cpts[node]
        factor = Factor(scope, np.array(cpt))
        
        # 乘以所有入消息
        for msg in incoming:
            factor = factor.multiply(msg)
        
        # 边际化除目标变量外的所有变量
        if parent in factor.scope:
            factor = factor.marginalize(node)
        
        # 归一化
        vals = factor.values.flatten()
        if np.sum(vals) > 0:
            vals = vals / np.sum(vals)
        factor.values = vals.reshape(factor.values.shape)
        
        return factor
    
    # 迭代传播
    for iteration in range(max_iter):
        changed = False
        
        for parent, child in bn.edges:
            msg = send_message(child, parent)
            old_msg = messages.get((child, parent))
            if old_msg is None or not np.allclose(old_msg.values, msg.values):
                changed = True
            messages[(child, parent)] = msg
        
        if not changed:
            break
    
    # 计算查询变量的信念
    query_factors = []
    
    # 乘以来自所有子节点的消息
    for child in bn.children[query_var]:
        if (child, query_var) in messages:
            query_factors.append(messages[(child, query_var)])
    
    # 获取查询变量的先验/CPT
    cpt = bn.cpts[query_var]
    factor = Factor([query_var], np.array(cpt))
    
    # 乘以所有消息
    for f in query_factors:
        factor = factor.multiply(f)
    
    # 归一化
    vals = factor.values.flatten()
    if np.sum(vals) > 0:
        vals = vals / np.sum(vals)
    
    return {i: float(p) for i, p in enumerate(vals)}


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("贝叶斯网络测试")
    print("=" * 60)
    
    # 构建一个简单的贝叶斯网络：地震报警器
    # 变量: B(Burglary), E(Earthquake), A(Alarm), J(John calls), M(Mary calls)
    # 拓扑顺序: B -> A, E -> A, A -> J, A -> M
    
    variables = ['B', 'E', 'A', 'J', 'M']
    edges = [('B', 'A'), ('E', 'A'), ('A', 'J'), ('A', 'M')]
    
    # 先验概率 P(B), P(E)
    cpts = {
        'B': [0.99, 0.01],  # P(B=true)=0.01
        'E': [0.98, 0.02],  # P(E=true)=0.02
        # P(A | B, E): B=0,E=0 -> A=1概率低; B=0,E=1; B=1,E=0; B=1,E=1
        'A': [
            # A=0 (alarm off)
            [0.999, 0.71, 0.06, 0.05],  # A=0 given B,E
            # A=1 (alarm on)  
            [0.001, 0.29, 0.94, 0.95],  # A=1 given B,E
        ],
        # P(J | A)
        'J': [
            [0.95, 0.10],  # J=0 given A
            [0.05, 0.90],  # J=1 given A
        ],
        # P(M | A)
        'M': [
            [0.99, 0.30],  # M=0 given A
            [0.01, 0.70],  # M=1 given A
        ],
    }
    
    # 创建网络
    bn = BayesianNetwork(variables, edges, cpts)
    
    print("\n1. 拓扑排序:", bn.topological_order())
    
    # 测试变量消除
    print("\n2. 变量消除算法测试:")
    print("   查询: P(B | J=1, M=1)")
    result = variable_elimination(bn, 'B', {'J': 1, 'M': 1})
    print(f"   P(B=0 | J=1, M=1) = {result[0]:.6f}")
    print(f"   P(B=1 | J=1, M=1) = {result[1]:.6f}")
    
    print("\n3. 变量消除算法:")
    print("   查询: P(A | J=1)")
    result = variable_elimination(bn, 'A', {'J': 1})
    print(f"   P(A=0 | J=1) = {result[0]:.6f}")
    print(f"   P(A=1 | J=1) = {result[1]:.6f}")
    
    print("\n4. 因子运算测试:")
    f1 = Factor(['X', 'Y'], np.array([[0.9, 0.3], [0.1, 0.7]]))
    f2 = Factor(['Y', 'Z'], np.array([[0.8], [0.2]]))
    f3 = f1.multiply(f2)
    print(f"   因子1 scope: {f1.scope}, shape: {f1.values.shape}")
    print(f"   因子2 scope: {f2.scope}, shape: {f2.values.shape}")
    print(f"   乘积因子 scope: {f3.scope}, shape: {f3.values.shape}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
