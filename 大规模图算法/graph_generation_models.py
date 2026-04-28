"""
图生成模型 (Graph Generation Models)
====================================
实现简单的图生成算法，包括随机图模型和基于统计的图生成。

模型：
1. Erdős-Rényi (ER) 随机图
2. Barabási-Albert (BA) 无标度网络
3. Watts-Strogatz (WS) 小世界网络
4. 配置模型 (Configuration Model)

参考：
    - Erdős, P. & Rényi, A. (1959). On random graphs.
    - Barabási, A.L. & Albert, R. (1999). Emergence of scaling in random networks.
    - Watts, D.J. & Strogatz, S.H. (1998). Collective dynamics of 'small-world' networks.
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
import random
import math


class Graph:
    """无向图"""
    def __init__(self, n: int = 0):
        self.n = n
        self.adj = [set() for _ in range(n)]
    
    def add_edge(self, u: int, v: int):
        self.adj[u].add(v)
        self.adj[v].add(u)
    
    def neighbors(self, u: int) -> Set[int]:
        return self.adj[u]
    
    def degree(self, u: int) -> int:
        return len(self.adj[u])
    
    def edge_count(self) -> int:
        return sum(self.degree(i) for i in range(self.n)) // 2


class RandomGraphGenerator:
    """
    随机图生成器基类
    """
    
    def __init__(self, n: int, seed: int = 42):
        self.n = n
        self.seed = seed
        random.seed(seed)
    
    def generate(self) -> Graph:
        """生成图"""
        raise NotImplementedError


class ErdősRényiGenerator(RandomGraphGenerator):
    """
    Erdős-Rényi 随机图模型 G(n, p)
    
    每对节点以概率p连接
    
    参数:
        n: 节点数
        p: 连边概率
        seed: 随机种子
    """
    
    def __init__(self, n: int, p: float, seed: int = 42):
        super().__init__(n, seed)
        self.p = p
    
    def generate(self) -> Graph:
        """生成ER随机图"""
        g = Graph(self.n)
        
        for u in range(self.n):
            for v in range(u + 1, self.n):
                if random.random() < self.p:
                    g.add_edge(u, v)
        
        return g


class BarabásiAlbertGenerator(RandomGraphGenerator):
    """
    Barabási-Albert 无标度网络生成模型
    
    优先连接： 新节点更可能连接到高度数节点
    
    参数:
        n: 目标节点数
        m: 每个新节点连接的边数
        seed: 随机种子
    """
    
    def __init__(self, n: int, m: int, seed: int = 42):
        super().__init__(n, seed)
        self.m = m  # 每个新节点添加的边数
    
    def generate(self) -> Graph:
        """生成BA无标度网络"""
        if self.n < 2:
            return Graph(self.n)
        
        g = Graph(self.n)
        
        # 初始完全图（m0个节点）
        m0 = min(self.m, self.n - 1)
        for i in range(m0):
            for j in range(i + 1, m0):
                g.add_edge(i, j)
        
        # 添加剩余节点
        for new_node in range(m0, self.n):
            # 计算度数和总度数
            degrees = [(i, g.degree(i)) for i in range(new_node)]
            total_degree = sum(d for _, d in degrees)
            
            if total_degree == 0:
                # 第一个节点随机连一条边
                target = random.randint(0, new_node - 1)
                g.add_edge(new_node, target)
            else:
                # 优先连接
                targets = set()
                
                while len(targets) < min(self.m, new_node):
                    # 按度数比例选择
                    r = random.random() * total_degree
                    cumsum = 0
                    
                    for i, d in degrees:
                        if i not in targets:
                            cumsum += d
                            if cumsum >= r:
                                targets.add(i)
                                break
                
                for target in targets:
                    g.add_edge(new_node, target)
        
        return g


class WattsStrogatzGenerator(RandomGraphGenerator):
    """
    Watts-Strogatz 小世界网络生成模型
    
    参数:
        n: 节点数（最好远大于k）
        k: 每个节点的近邻数（偶数）
        beta: 重新连线概率
        seed: 随机种子
    """
    
    def __init__(self, n: int, k: int, beta: float, seed: int = 42):
        super().__init__(n, seed)
        self.k = k  # 近邻数
        self.beta = beta  # 重连概率
    
    def generate(self) -> Graph:
        """生成WS小世界网络"""
        if self.n <= self.k:
            return Graph(self.n)
        
        g = Graph(self.n)
        
        # 创建环形网格
        for i in range(self.n):
            for j in range(1, self.k // 2 + 1):
                target = (i + j) % self.n
                g.add_edge(i, target)
        
        # 重新连线
        for i in range(self.n):
            for j in range(1, self.k // 2 + 1):
                source = i
                target = (i + j) % self.n
                
                if random.random() < self.beta:
                    # 删除原边
                    g.adj[source].discard(target)
                    g.adj[target].discard(source)
                    
                    # 添加新边（不能是自环或重边）
                    new_target = random.randint(0, self.n - 1)
                    attempts = 0
                    
                    while (new_target == source or 
                           new_target in g.adj[source] or
                           new_target in g.adj[source] or
                           attempts < 100):
                        new_target = random.randint(0, self.n - 1)
                        attempts += 1
                    
                    g.add_edge(source, new_target)
        
        return g


class ConfigurationModelGenerator(RandomGraphGenerator):
    """
    配置模型生成器
    
    根据给定的度序列生成随机图
    
    参数:
        degree_sequence: 度序列
        seed: 随机种子
    """
    
    def __init__(self, degree_sequence: List[int], seed: int = 42):
        n = len(degree_sequence)
        super().__init__(n, seed)
        self.degree_sequence = degree_sequence
    
    def generate(self) -> Optional[Graph]:
        """生成配置模型图"""
        n = self.n
        
        # 检查度序列可行性
        if sum(self.degree_sequence) % 2 != 0:
            return None  # 度数和必须为偶数
        
        # 创建stub列表
        stubs = []
        for node in range(n):
            stubs.extend([node] * self.degree_sequence[node])
        
        random.shuffle(stubs)
        
        g = Graph(n)
        
        # 配对
        for i in range(0, len(stubs) - 1, 2):
            u, v = stubs[i], stubs[i + 1]
            
            if u != v and v not in g.adj[u]:
                g.add_edge(u, v)
        
        return g


class StochasticBlockModelGenerator(RandomGraphGenerator):
    """
    随机块模型 (SBM)
    
    参数:
        n: 节点数
        k: 社区数
        p: 社区内连边概率
        q: 社区间连边概率
        seed: 随机种子
    """
    
    def __init__(self, n: int, k: int, p: float, q: float, seed: int = 42):
        super().__init__(n, seed)
        self.k = k
        self.p = p  # 社区内概率
        self.q = q  # 社区间概率
    
    def generate(self) -> Tuple[Graph, List[int]]:
        """
        生成SBM图
        
        返回:
            (图, 社区标签)
        """
        g = Graph(self.n)
        
        # 分配社区
        community_size = self.n // self.k
        labels = []
        
        for i in range(self.n):
            label = min(i // community_size, self.k - 1)
            labels.append(label)
        
        # 生成边
        for u in range(self.n):
            for v in range(u + 1, self.n):
                if labels[u] == labels[v]:
                    prob = self.p
                else:
                    prob = self.q
                
                if random.random() < prob:
                    g.add_edge(u, v)
        
        return g, labels


def generate_random_graph(model: str, n: int, **kwargs) -> Graph:
    """
    便捷函数：生成随机图
    
    参数:
        model: 模型类型 ("er", "ba", "ws", "sbm")
        n: 节点数
        **kwargs: 模型参数
    
    返回:
        生成的图
    """
    if model == "er":
        p = kwargs.get("p", 0.5)
        return ErdősRényiGenerator(n, p).generate()
    
    elif model == "ba":
        m = kwargs.get("m", 2)
        return BarabásiAlbertGenerator(n, m).generate()
    
    elif model == "ws":
        k = kwargs.get("k", 4)
        beta = kwargs.get("beta", 0.3)
        return WattsStrogatzGenerator(n, k, beta).generate()
    
    elif model == "sbm":
        k = kwargs.get("k", 2)
        p = kwargs.get("p", 0.5)
        q = kwargs.get("q", 0.1)
        return StochasticBlockModelGenerator(n, k, p, q).generate()[0]
    
    else:
        raise ValueError(f"Unknown model: {model}")


if __name__ == "__main__":
    print("=== 图生成模型测试 ===")
    
    # Erdős-Rényi
    print("\n--- Erdős-Rényi G(20, 0.3) ---")
    er_gen = ErdősRényiGenerator(20, 0.3, seed=42)
    g_er = er_gen.generate()
    print(f"节点: {g_er.n}, 边: {g_er.edge_count()}")
    
    # Barabási-Albert
    print("\n--- Barabási-Albert (n=20, m=2) ---")
    ba_gen = BarabásiAlbertGenerator(20, 2, seed=42)
    g_ba = ba_gen.generate()
    print(f"节点: {g_ba.n}, 边: {g_ba.edge_count()}")
    
    # 度分布
    degrees_ba = [g_ba.degree(i) for i in range(g_ba.n)]
    print(f"度分布: min={min(degrees_ba)}, max={max(degrees_ba)}, "
          f"avg={sum(degrees_ba)/len(degrees_ba):.2f}")
    
    # Watts-Strogatz
    print("\n--- Watts-Strogatz (n=20, k=4, beta=0.3) ---")
    ws_gen = WattsStrogatzGenerator(20, 4, 0.3, seed=42)
    g_ws = ws_gen.generate()
    print(f"节点: {g_ws.n}, 边: {g_ws.edge_count()}")
    
    # Stochastic Block Model
    print("\n--- Stochastic Block Model (n=20, k=2, p=0.6, q=0.1) ---")
    sbm_gen = StochasticBlockModelGenerator(20, 2, 0.6, 0.1, seed=42)
    g_sbm, labels = sbm_gen.generate()
    print(f"节点: {g_sbm.n}, 边: {g_sbm.edge_count()}")
    print(f"社区分配: {labels}")
    
    # 便捷函数
    print("\n--- 便捷函数 ---")
    g = generate_random_graph("er", n=15, p=0.2)
    print(f"ER(15, 0.2): {g.n} 节点, {g.edge_count()} 边")
    
    g2 = generate_random_graph("ba", n=15, m=3)
    print(f"BA(15, 3): {g2.n} 节点, {g2.edge_count()} 边")
    
    # 配置模型
    print("\n--- Configuration Model ---")
    degree_seq = [3, 2, 2, 2, 1]  # 度序列（和必须为偶数）
    conf_gen = ConfigurationModelGenerator(degree_seq, seed=42)
    g_conf = conf_gen.generate()
    if g_conf:
        print(f"度序列 {degree_seq} 生成了 {g_conf.n} 节点, {g_conf.edge_count()} 边")
    else:
        print(f"度序列 {degree_seq} 不可行")
    
    print("\n=== 测试完成 ===")
