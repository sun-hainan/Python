"""
信念传播算法：精确与近似实现
Belief Propagation: Exact and Approximate Implementation

信念传播通过在贝叶斯网络节点间传递消息来计算边缘概率。
对于树状结构网络，精确信念传播收敛很快；
对于一般图，使用Loopy Belief Propagation近似求解。
"""

import numpy as np
from collections import defaultdict
from typing import Dict, List, Tuple, Optional


class Factor:
    """因子类：表示变量子集上的势函数"""
    
    def __init__(self, scope: List[str], values: np.ndarray):
        self.scope = scope
        self.values = values
        self.var_index = {var: i for i, var in enumerate(scope)}
    
    def marginalize(self, var: str) -> 'Factor':
        """边际化：消除变量var"""
        if var not in self.var_index:
            return Factor(self.scope.copy(), self.values.copy())
        
        dim = self.var_index[var]
        new_scope = [v for v in self.scope if v != var]
        new_values = np.sum(self.values, axis=dim)
        
        return Factor(new_scope, new_values)
    
    def multiply(self, other: 'Factor') -> 'Factor':
        """因子相乘"""
        all_vars = list(set(self.scope) | set(other.scope))
        all_vars.sort(key=lambda v: self.var_index.get(v, other.var_index.get(v, 0)))
        
        self_axes = [all_vars.index(v) for v in self.scope]
        other_axes = [all_vars.index(v) for v in other.scope]
        
        result = np.einsum(self.values, self_axes, other.values, other_axes, all_vars)
        return Factor(all_vars, result)
    
    def normalize(self) -> 'Factor':
        """归一化因子"""
        vals = self.values.flatten()
        total = np.sum(vals)
        if total > 0:
            vals = vals / total
        new_values = vals.reshape(self.values.shape)
        return Factor(self.scope, new_values)


class BeliefPropagation:
    """
    信念传播算法
    
    支持：
    - 精确信念传播（树状网络）
    - Loopy信念传播（一般图近似）
    """
    
    def __init__(self, network: 'BayesianNetwork'):
        self.network = network
        self.messages = {}  # 消息缓存: (from_node, to_node) -> Factor
        self.beliefs = {}  # 节点信念: node -> Factor
        self.max_iter = 100  # 最大迭代次数
        self.tolerance = 1e-6  # 收敛容差
    
    def init_messages(self):
        """初始化所有消息为均匀分布"""
        self.messages = {}
        
        for node in self.network.variables:
            # 初始化传入消息
            for parent in self.network.parents[node]:
                scope = [parent]
                values = np.ones(2) / 2  # 均匀分布
                self.messages[(parent, node)] = Factor(scope, values)
    
    def get_lambda_messages(self, node: str) -> List[Factor]:
        """
        获取从子节点传来的lambda消息
        
        参数:
            node: 目标节点
            
        返回:
            lambda消息列表
        """
        lambdas = []
        for child in self.network.children[node]:
            if (child, node) in self.messages:
                lambdas.append(self.messages[(child, node)])
        return lambdas
    
    def get_pi_messages(self, node: str) -> List[Factor]:
        """
        获取从父节点传来的pi消息
        
        参数:
            node: 目标节点
            
        返回:
            pi消息列表
        """
        pis = []
        for parent in self.network.parents[node]:
            if (parent, node) in self.messages:
                pis.append(self.messages[(parent, node)])
        return pis
    
    def compute_pi(self, node: str) -> Factor:
        """
        计算节点的pi消息（从父节点的信念）
        
        参数:
            node: 节点名
            
        返回:
            pi因子
        """
        if not self.network.parents[node]:
            # 没有父节点，使用先验
            values = np.array(self.network.cpts[node])
            return Factor([node], values)
        
        # 获取CPT
        scope = self.network.parents[node] + [node]
        values = np.array(self.network.cpts[node])
        factor = Factor(scope, values)
        
        # 乘以所有父节点的pi消息
        for parent in self.network.parents[node]:
            if (parent, node) in self.messages:
                pi_msg = self.messages[(parent, node)]
                factor = factor.multiply(pi_msg)
        
        # 边缘化子节点维度
        factor = factor.marginalize(node)
        
        # 归一化
        factor = factor.normalize()
        
        return factor
    
    def compute_lambda(self, node: str) -> Factor:
        """
        计算节点的lambda消息（发送给父节点）
        
        参数:
            node: 源节点
            
        返回:
            lambda消息
        """
        # 获取CPT
        scope = self.network.parents[node] + [node]
        values = np.array(self.network.cpts[node])
        factor = Factor(scope, values)
        
        # 乘以所有其他子节点传来的lambda
        for child in self.network.children[node]:
            for parent in self.network.parents[child]:
                if parent == node and (child, node) in self.messages:
                    factor = factor.multiply(self.messages[(child, node)])
        
        # 边际化
        factor = factor.marginalize(node)
        
        # 归一化
        factor = factor.normalize()
        
        return factor
    
    def send_message(self, from_node: str, to_node: str):
        """
        从from_node向to_node发送消息
        
        参数:
            from_node: 发送节点
            to_node: 接收节点
        """
        if to_node in self.network.parents[from_node]:
            # from是子的父节点，发送pi消息
            pi = self.compute_pi(from_node)
            self.messages[(from_node, to_node)] = pi
        else:
            # from是子的子节点，发送lambda消息
            lam = self.compute_lambda(from_node)
            self.messages[(from_node, to_node)] = lam
    
    def update_beliefs(self):
        """更新所有节点的信念"""
        for node in self.network.variables:
            scope = [node]
            values = np.array(self.network.cpts.get(node, [0.5, 0.5]))
            
            # 乘以传入消息
            factor = Factor(scope, values)
            
            for child in self.network.children[node]:
                if (child, node) in self.messages:
                    factor = factor.multiply(self.messages[(child, node)])
            
            self.beliefs[node] = factor.normalize()
    
    def run_exact(self) -> bool:
        """
        运行精确信念传播（仅适用于树状网络）
        
        返回:
            是否收敛
        """
        self.init_messages()
        
        # 找到根节点（无父节点的节点）
        roots = [v for v in self.network.variables if not self.network.parents[v]]
        
        # 自底向上传递lambda
        for root in roots:
            self._propagate_lambda_up(root)
        
        # 自顶向下传递pi
        for root in roots:
            self._propagate_pi_down(root)
        
        # 更新信念
        self.update_beliefs()
        
        return True
    
    def _propagate_lambda_up(self, node: str):
        """自底向上传播lambda消息"""
        for parent in self.network.parents[node]:
            # 计算并发送lambda消息
            lam = self.compute_lambda(node)
            self.messages[(node, parent)] = lam
            # 递归
            self._propagate_lambda_up(parent)
    
    def _propagate_pi_down(self, node: str):
        """自顶向下传播pi消息"""
        for child in self.network.children[node]:
            pi = self.compute_pi(child)
            self.messages[(node, child)] = pi
            self._propagate_pi_down(child)
    
    def run_loopy(self) -> Tuple[bool, int]:
        """
        运行Loopy信念传播（适用于一般图）
        
        返回:
            (是否收敛, 迭代次数)
        """
        self.init_messages()
        
        for iteration in range(self.max_iter):
            old_messages = dict(self.messages)
            
            # 同步更新所有消息
            new_messages = {}
            
            for parent, child in self.network.edges:
                # 计算pi消息 (parent -> child)
                scope = self.network.parents[child] + [child]
                values = np.array(self.network.cpts[child])
                factor = Factor(scope, values)
                
                for p in self.network.parents[child]:
                    if (p, child) in self.messages:
                        factor = factor.multiply(self.messages[(p, child)])
                
                factor = factor.marginalize(child)
                factor = factor.normalize()
                new_messages[(parent, child)] = factor
                
                # 计算lambda消息 (child -> parent)
                scope2 = self.network.parents[child] + [child]
                values2 = np.array(self.network.cpts[child])
                factor2 = Factor(scope2, values2)
                
                for c in self.network.children[child]:
                    if (c, child) in self.messages:
                        factor2 = factor2.multiply(self.messages[(c, child)])
                
                factor2 = factor2.marginalize(child)
                factor2 = factor2.normalize()
                new_messages[(child, parent)] = factor2
            
            self.messages = new_messages
            
            # 检查收敛
            max_diff = 0
            for key in self.messages:
                if key in old_messages:
                    diff = np.max(np.abs(
                        self.messages[key].values - old_messages[key].values
                    ))
                    max_diff = max(max_diff, diff)
            
            if max_diff < self.tolerance:
                self.update_beliefs()
                return True, iteration + 1
        
        self.update_beliefs()
        return False, self.max_iter
    
    def query(self, var: str, evidence: Optional[Dict[str, int]] = None) -> Dict[int, float]:
        """
        查询边缘概率
        
        参数:
            var: 查询变量
            evidence: 证据
            
        返回:
            边缘概率分布
        """
        evidence = evidence or {}
        
        # 如果有证据，设置证据节点的信念
        for ev_var, ev_val in evidence.items():
            scope = [ev_var]
            values = np.zeros(2)
            values[ev_val] = 1.0
            self.beliefs[ev_var] = Factor(scope, values)
        
        # 运行信念传播
        if self._is_tree():
            self.run_exact()
        else:
            self.run_loopy()
        
        # 返回查询变量的信念
        if var in self.beliefs:
            beliefs = self.beliefs[var].values.flatten()
            return {i: float(p) for i, p in enumerate(beliefs)}
        else:
            return {0: 0.5, 1: 0.5}
    
    def _is_tree(self) -> bool:
        """检查网络是否是树状结构"""
        # 简单检查：每个节点最多只有一个父节点
        for node in self.network.variables:
            if len(self.network.parents[node]) > 1:
                return False
        return True


class BayesianNetwork:
    """简化的贝叶斯网络"""
    
    def __init__(self):
        self.variables = []
        self.parents = defaultdict(list)
        self.children = defaultdict(list)
        self.cpts = {}
        self.edges = []


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("信念传播算法测试")
    print("=" * 60)
    
    # 创建测试网络：简单串联
    # A -> B -> C
    variables = ['A', 'B', 'C']
    edges = [('A', 'B'), ('B', 'C')]
    
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
    
    bn = BayesianNetwork()
    bn.variables = variables
    bn.edges = edges
    bn.parents = defaultdict(list, {'B': ['A'], 'C': ['B']})
    bn.children = defaultdict(list, {'A': ['B'], 'B': ['C']})
    bn.cpts = cpts
    
    bp = BeliefPropagation(bn)
    
    print("\n1. 精确信念传播（树状网络）:")
    print("   查询 P(A | C=1)")
    result = bp.query('A', evidence={'C': 1})
    print(f"   P(A=0 | C=1) = {result[0]:.4f}")
    print(f"   P(A=1 | C=1) = {result[1]:.4f}")
    
    print("\n2. 信念传播测试:")
    print("   查询 P(B)")
    bp2 = BeliefPropagation(bn)
    result = bp2.query('B')
    print(f"   P(B=0) = {result[0]:.4f}")
    print(f"   P(B=1) = {result[1]:.4f}")
    
    print("\n3. Loopy信念传播测试:")
    # 创建有环的测试网络
    bn3 = BayesianNetwork()
    bn3.variables = ['X', 'Y', 'Z']
    bn3.edges = [('X', 'Y'), ('Y', 'Z'), ('Z', 'X')]  # 三角环
    bn3.parents = defaultdict(list, {'Y': ['X'], 'Z': ['Y'], 'X': ['Z']})
    bn3.children = defaultdict(list, {'X': ['Y'], 'Y': ['Z'], 'Z': ['X']})
    bn3.cpts = {
        'X': [0.5, 0.5],
        'Y': [[0.7, 0.3], [0.3, 0.7]],
        'Z': [[0.6, 0.4], [0.4, 0.6]],
    }
    
    bp3 = BeliefPropagation(bn3)
    converged, iterations = bp3.run_loopy()
    print(f"   收敛: {converged}, 迭代次数: {iterations}")
    result = bp3.query('X')
    print(f"   P(X=0) = {result[0]:.4f}")
    print(f"   P(X=1) = {result[1]:.4f}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
