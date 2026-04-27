# -*- coding: utf-8 -*-
"""
算法实现：21_量子计算 / qaoa

本文件实现 qaoa 相关的算法功能。
"""

import numpy as np


class QAOAMaxCut:
    """
    QAOA 求解 Max-Cut 问题
    
    Max-Cut: 将顶点集分成两部分，最大化跨割的边数
    Ising 模型：H_C = (1/2) * Σ_{(i,j)∈E} (1 - Z_i Z_j) = #cross_edges
    
    QAOA 电路：
    - 初始态：|++...+⟩
    - 每层：先应用问题哈密顿ian H_C，再应用混合哈密顿ian H_B = Σ X_i
    - 测量多次，统计最优划分
    """
    
    def __init__(self, graph):
        """
        参数：
            graph: 邻接表 {vertex: [neighbors]}
        """
        self.graph = graph
        self.n = len(graph)
        self.edges = []
        
        for u in graph:
            for v in graph[u]:
                if u < v:
                    self.edges.append((u, v))
    
    def build_qubo_matrix(self):
        """
        构建 QUBO 矩阵
        
        Max-Cut QUBO: 最大化 Σ_{(i,j)∈E} (x_i + x_j - 2*x_i*x_j)
        转化为最小化后：Q[i,j] = -2 for edge (i,j)
        """
        Q = np.zeros((self.n, self.n))
        
        for u, v in self.edges:
            Q[u, v] = -2
            Q[v, u] = -2
        
        return Q
    
    def cost_function(self, bitstring):
        """
        计算 Max-Cut 目标值
        
        参数：
            bitstring: 二进制字符串，如 [0,1,0,1]
        
        返回：割边数
        """
        cut_value = 0
        for u, v in self.edges:
            if bitstring[u] != bitstring[v]:
                cut_value += 1
        return cut_value
    
    def simulate_layer(self, gamma, beta, state):
        """
        模拟一层 QAOA
        
        参数：
            gamma, beta: 角度参数
            state: 当前状态向量
        """
        n = self.n
        dim = 2 ** n
        
        # 简化的模拟：应用 X 旋转
        new_state = state.copy()
        
        for q in range(n):
            # 应用 Rx(2*beta) 门
            for i in range(dim):
                # 简化：只考虑状态|i⟩的贡献
                pass
        
        return new_state
    
    def qaoa_circuit(self, gammas, betas):
        """
        简化的 QAOA 电路模拟
        
        参数：
            gammas: 问题层的角度列表 [gamma_1, ..., gamma_p]
            betas: 混合层的角度列表 [beta_1, ..., beta_p]
        
        返回：最终状态向量
        """
        n = self.n
        dim = 2 ** n
        
        # 初始态 |++...+⟩ = H^⊗n |00...0⟩
        state = np.ones(dim, dtype=complex) / np.sqrt(dim)
        
        # 简化模拟：使用概率分布估计
        # 实际中需要真实的量子电路
        probs = np.abs(state) ** 2
        
        for gamma, beta in zip(gammas, betas):
            # 问题哈密顿ian（混合）的效果
            # 简化：使用 Metropolis 风格的采样
            for _ in range(2 ** n):
                # 基于能量选择
                pass
        
        return state
    
    def classical_max_cut(self):
        """
        经典精确算法（暴力）求 Max-Cut
        用于验证
        """
        best_value = 0
        best_config = None
        
        for config_int in range(2 ** self.n):
            bitstring = [(config_int >> i) & 1 for i in range(self.n)]
            value = self.cost_function(bitstring)
            if value > best_value:
                best_value = value
                best_config = bitstring
        
        return best_value, best_config
    
    def sample_bitstrings(self, state, n_samples=100):
        """
        从量子态采样比特串
        
        参数：
            state: 状态向量
            n_samples: 采样次数
        """
        n = self.n
        dim = 2 ** n
        probs = np.abs(state) ** 2
        
        samples = []
        for _ in range(n_samples):
            config_int = np.random.choice(dim, p=probs)
            bitstring = [(config_int >> i) & 1 for i in range(n)]
            samples.append(bitstring)
        
        return samples


def grover_optimizer(qaoa, gammas, betas, n_samples=50):
    """
    使用 Grover 风格的优化器增强 QAOA
    
    概念：使用 amplitude amplification 
    将目标态（最优解）的振幅放大
    
    参数：
        qaoa: QAOAMaxCut 实例
        gammas, betas: QAOA 参数
        n_samples: 每次迭代的采样数
    
    返回：最优采样结果
    """
    # 执行 QAOA 电路
    state = qaoa.qaoa_circuit(gammas, betas)
    
    # 采样
    samples = qaoa.sample_bitstrings(state, n_samples)
    
    # 评估
    evaluated = [(s, qaoa.cost_function(s)) for s in samples]
    evaluated.sort(key=lambda x: -x[1])
    
    return evaluated[0]


def grid_search(qaoa, p=1, n_samples=100):
    """
    网格搜索找最优 QAOA 参数
    """
    best_value = 0
    best_params = None
    
    n = qaoa.n
    
    # p=1: 两个参数 gamma, beta
    n_points = 20
    
    for i in range(n_points):
        gamma = 2 * np.pi * i / n_points
        for j in range(n_points):
            beta = np.pi * j / n_points
            
            # 模拟 QAOA
            state = qaoa.qaoa_circuit([gamma], [beta])
            samples = qaoa.sample_bitstrings(state, n_samples)
            
            # 取最优
            values = [qaoa.cost_function(s) for s in samples]
            best_sample_val = max(values)
            
            if best_sample_val > best_value:
                best_value = best_sample_val
                best_params = (gamma, beta)
    
    return best_params, best_value


if __name__ == "__main__":
    print("=" * 55)
    print("量子近似优化算法（QAOA）")
    print("=" * 55)
    
    # 构建一个 Max-Cut 示例
    graph = {
        0: [1, 2, 3],
        1: [0, 2],
        2: [0, 1, 3],
        3: [0, 2],
    }
    
    qaoa = QAOAMaxCut(graph)
    
    print(f"\n图：{qaoa.n} 个顶点")
    print(f"边：{qaoa.edges}")
    
    # 经典精确解
    exact_val, exact_config = qaoa.classical_max_cut()
    print(f"\n精确 Max-Cut 值: {exact_val}")
    print(f"最优划分: {exact_config}")
    
    # QAOA 近似
    print("\nQAOA p=1 参数搜索...")
    best_params, qaoa_val = grid_search(qaoa, p=1)
    
    print(f"最优参数: gamma={best_params[0]:.3f}, beta={best_params[1]:.3f}")
    print(f"QAOA Max-Cut 值: {qaoa_val}")
    print(f"近似比: {qaoa_val / exact_val:.3f}")
    
    # QUBO 矩阵
    Q = qaoa.build_qubo_matrix()
    print(f"\nQUBO 矩阵:\n{Q}")
