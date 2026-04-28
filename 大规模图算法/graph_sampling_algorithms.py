"""
图采样算法 (Graph Sampling Algorithms)
========================================
实现多种大规模图采样算法：

1. Node2Vec采样：结合DFS和BFS的偏置随机游走
2. GraphSAINT：基于节点/边/循环保真度的图采样
3. ForestFire：模拟火灾蔓延的图采样

参考：
    - Grover, A. & Leskovec, J. (2016). node2vec: Scalable feature learning.
    - Zeng, J. et al. (2019). GraphSAINT: Graph Sampling Based Inductive Learning.
    - Leskovec, J. et al. (2005). Graphs over Time: Densification Laws.
"""

from typing import List, Dict, Set, Optional, Tuple
from collections import deque
import random
import copy


class Graph:
    """图数据结构（支持有向/无向）"""
    
    def __init__(self, n: int = 0, directed: bool = False):
        self.n = n  # 节点数量
        self.directed = directed  # 是否为有向图
        self.adj = [set() for _ in range(n)]  # 邻接表
    
    def add_edge(self, u: int, v: int):
        """添加边 u -> v"""
        self.adj[u].add(v)
        if not self.directed:
            self.adj[v].add(u)
    
    def neighbors(self, u: int) -> List[int]:
        """返回节点u的邻居列表"""
        return list(self.adj[u])
    
    def out_degree(self, u: int) -> int:
        """返回节点u的出度"""
        return len(self.adj[u])


# ==================== Node2Vec 采样 ====================

class Node2VecSampler:
    """
    Node2Vec偏置随机游走采样器
    
    参数:
        graph: 输入图
        p: 返回参数（Return parameter），控制返回前驱节点的概率
        q: 输入参数（In-out parameter），控制BFS/DFS倾向
    """
    
    def __init__(self, graph: Graph, p: float = 1.0, q: float = 1.0):
        self.graph = graph
        self.p = p  # 返回参数
        self.q = q  # 进出参数
    
    def _compute_alias_table(self, probs: List[float]) -> Tuple[List[int], List[float]]:
        """
        构建别名表以实现O(1)复杂度的离散采样
        
        参数:
            probs: 各选项的概率分布（未归一化）
        
        返回:
            (别名表, 概率表)
        """
        n = len(probs)
        total = sum(probs)
        # 归一化概率
        normalized = [p / total for p in probs]
        
        # 构建别名表
        small = []  # 概率 < 1 的索引
        large = []  # 概率 >= 1 的索引
        
        for i, prob in enumerate(normalized):
            if prob < 1.0:
                small.append((i, prob))
            else:
                large.append((i, prob))
        
        alias = [0] * n
        prob_table = [0.0] * n
        
        while small and large:
            s_idx, s_prob = small.pop()
            l_idx, l_prob = large.pop()
            
            alias[s_idx] = l_idx
            prob_table[s_idx] = s_prob
            l_prob = l_prob - (1.0 - s_prob)
            
            if l_prob < 1.0:
                small.append((l_idx, l_prob))
            else:
                large.append((l_idx, l_prob))
        
        while small:
            s_idx, s_prob = small.pop()
            prob_table[s_idx] = s_prob
        
        while large:
            l_idx, _ = large.pop()
            prob_table[l_idx] = 1.0
        
        return alias, prob_table
    
    def get_transition_probs(self, current: int, previous: int) -> List[Tuple[int, float]]:
        """
        计算从current节点的转移概率分布
        
        参数:
            current: 当前节点
            previous: 前驱节点
        
        返回:
            [(下一节点, 概率), ...]
        """
        neighbors = self.graph.neighbors(current)
        if not neighbors:
            return []
        
        unnormalized_probs = []
        
        for neighbor in neighbors:
            # 计算最短距离
            if neighbor == previous:
                # 返回前驱节点（距离=0）
                dist = 0
            elif previous in self.graph.adj[neighbor]:
                # 是前驱的邻居（距离=1）
                dist = 1
            else:
                # 更远的节点（距离=2）
                dist = 2
            
            # 计算权重
            if dist == 0:
                weight = 1.0 / self.p
            elif dist == 1:
                weight = 1.0
            else:  # dist == 2
                weight = 1.0 / self.q
            
            unnormalized_probs.append((neighbor, weight))
        
        # 归一化
        total = sum(w for _, w in unnormalized_probs)
        normalized = [(n, w / total) for n, w in unnormalized_probs]
        
        return normalized
    
    def simulate_walk(self, start: int, walk_length: int) -> List[int]:
        """
        模拟一次随机游走
        
        参数:
            start: 起始节点
            walk_length: 游走长度
        
        返回:
            游走路径（节点序列）
        """
        walk = [start]
        current = start
        previous = None
        
        for _ in range(walk_length - 1):
            neighbors = self.graph.neighbors(current)
            if not neighbors:
                break
            
            # 计算转移概率
            if previous is None:
                # 第一步：均匀分布
                probs = [(n, 1.0 / len(neighbors)) for n in neighbors]
            else:
                probs = self.get_transition_probs(current, previous)
            
            # 采样下一个节点
            nodes = [n for n, _ in probs]
            weights = [w for _, w in probs]
            current = random.choices(nodes, weights=weights, k=1)[0]
            
            previous = current
            walk.append(current)
        
        return walk
    
    def sample_walks(self, num_walks: int, walk_length: int, 
                     start_nodes: Optional[List[int]] = None) -> List[List[int]]:
        """
        采样多条游走路径
        
        参数:
            num_walks: 每节点的游走次数
            walk_length: 游走长度
            start_nodes: 起始节点列表（None表示所有节点）
        
        返回:
            所有游走路径的列表
        """
        if start_nodes is None:
            start_nodes = list(range(self.graph.n))
        
        walks = []
        for _ in range(num_walks):
            random.shuffle(start_nodes)
            for start in start_nodes:
                walk = self.simulate_walk(start, walk_length)
                walks.append(walk)
        
        return walks


# ==================== GraphSAINT 采样 ====================

class GraphSAINTSampler:
    """
    GraphSAINT图采样器
    
    支持三种采样方法：
    - 节点采样 (NodeSampler)：按节点概率采样
    - 边采样 (EdgeSampler)：按边概率采样
    - 循环保真采样 (RingSampler)：按二跳邻居结构采样
    
    参数:
        graph: 输入图
        sample_size: 采样子图的期望大小
        num_samples: 采样次数
    """
    
    def __init__(self, graph: Graph, sample_size: int = 1000, 
                 method: str = "node"):
        self.graph = graph
        self.sample_size = sample_size
        self.method = method
        
        # 预计算节点和边的权重
        self._compute_sampling_weights()
    
    def _compute_sampling_weights(self):
        """计算采样权重"""
        n = self.graph.n
        
        # 节点度数
        self.degrees = [self.graph.out_degree(i) for i in range(n)]
        
        # 归一化权重
        total_deg = sum(self.degrees)
        self.node_probs = [d / total_deg for d in self.degrees]
        
        # 边采样权重：每条边的权重为两端点的度数乘积
        self.edge_weights = []
        self.edge_list = []
        
        for u in range(n):
            for v in self.graph.adj[u]:
                if u < v:  # 避免重复
                    weight = self.degrees[u] * self.degrees[v]
                    self.edge_weights.append(weight)
                    self.edge_list.append((u, v))
        
        total_edge_weight = sum(self.edge_weights)
        self.edge_probs = [w / total_edge_weight for w in self.edge_weights]
    
    def node_sample(self) -> Set[int]:
        """
        节点采样
        
        返回:
            采样的节点集合
        """
        # 按度数概率采样节点
        sampled = set()
        
        while len(sampled) < self.sample_size:
            # 采样一个节点
            node = random.choices(range(self.graph.n), weights=self.node_probs, k=1)[0]
            sampled.add(node)
        
        return sampled
    
    def edge_sample(self) -> Set[int]:
        """
        边采样
        
        返回:
            采样的节点集合（通过边采样得到）
        """
        sampled = set()
        
        while len(sampled) < self.sample_size:
            # 按边权重采样一条边
            idx = random.choices(range(len(self.edge_list)), weights=self.edge_probs, k=1)[0]
            u, v = self.edge_list[idx]
            sampled.add(u)
            sampled.add(v)
        
        return sampled
    
    def _get_2hop_neighbors(self, nodes: Set[int]) -> Set[int]:
        """获取节点集合的二跳邻居"""
        neighbors = set()
        for u in nodes:
            for v in self.graph.adj[u]:
                neighbors.add(v)
        return neighbors
    
    def ring_sample(self) -> Set[int]:
        """
        循环保真采样 (2-hop sampling)
        
        采样节点的2-hop邻居，确保覆盖局部结构
        
        返回:
            采样的节点集合
        """
        # 首先采样一些"种子"节点
        seed_size = max(1, self.sample_size // 10)
        seeds = set(random.choices(range(self.graph.n), weights=self.node_probs, k=seed_size))
        
        # 获取2跳邻居
        sampled = seeds.copy()
        for seed in seeds:
            for v in self.graph.adj[seed]:
                sampled.add(v)
                for w in self.graph.adj[v]:
                    sampled.add(w)
        
        # 如果太大，随机剪枝
        if len(sampled) > self.sample_size * 1.5:
            sampled = set(random.sample(list(sampled), self.sample_size))
        
        return sampled
    
    def sample(self) -> Graph:
        """
        执行一次采样，返回采样的子图
        
        返回:
            采样的子图
        """
        if self.method == "node":
            sampled_nodes = self.node_sample()
        elif self.method == "edge":
            sampled_nodes = self.edge_sample()
        elif self.method == "ring":
            sampled_nodes = self.ring_sample()
        else:
            raise ValueError(f"Unknown method: {self.method}")
        
        # 构建子图
        subgraph = Graph(n=len(sampled_nodes), directed=self.graph.directed)
        
        # 创建节点索引映射
        node_map = {node: idx for idx, node in enumerate(sorted(sampled_nodes))}
        
        # 添加边
        for u in sampled_nodes:
            for v in self.graph.adj[u]:
                if v in sampled_nodes:
                    subgraph.add_edge(node_map[u], node_map[v])
        
        return subgraph
    
    def sample_normalized(self, num_samples: int = 10) -> List[Graph]:
        """
        执行多次采样并归一化
        
        参数:
            num_samples: 采样次数
        
        返回:
            归一化采样图列表
        """
        samples = [self.sample() for _ in range(num_samples)]
        return samples


# ==================== Forest Fire 采样 ====================

class ForestFireSampler:
    """
    Forest Fire 图采样器
    
    模拟火灾蔓延过程：随机选择一个起始节点，以一定概率"燃烧"其邻居，
    然后递归燃烧邻居的邻居。
    
    参数:
        graph: 输入图
        forward_prob: 前向燃烧概率（燃烧邻居）
        backward_prob: 后向燃烧概率（燃烧前驱）
        max_nodes: 最大采样节点数
    """
    
    def __init__(self, graph: Graph, forward_prob: float = 0.6, 
                 backward_prob: float = 0.3, max_nodes: int = 1000):
        self.graph = graph
        self.forward_prob = forward_prob
        self.backward_prob = backward_prob
        self.max_nodes = max_nodes
    
    def _burn_node(self, node: int, visited: Set[int], burned_edges: Set[Tuple[int, int]]):
        """
        递归燃烧过程
        
        参数:
            node: 当前燃烧节点
            visited: 已访问节点集合
            burned_edges: 燃烧的边集合
        """
        if len(visited) >= self.max_nodes:
            return
        
        visited.add(node)
        
        # 获取邻居
        neighbors = list(self.graph.adj[node])
        random.shuffle(neighbors)
        
        # 计算要燃烧的邻居数量
        num_to_burn = sum(1 for _ in neighbors if random.random() < self.forward_prob)
        
        burned = 0
        for neighbor in neighbors:
            if burned >= num_to_burn:
                break
            if neighbor not in visited:
                # 燃烧这条边
                burned_edges.add((node, neighbor) if node < neighbor else (neighbor, node))
                self._burn_node(neighbor, visited, burned_edges)
                burned += 1
    
    def sample(self, start_node: Optional[int] = None) -> Graph:
        """
        执行一次森林火灾采样
        
        参数:
            start_node: 起始节点（None表示随机选择）
        
        返回:
            采样的子图
        """
        if start_node is None:
            start_node = random.randint(0, self.graph.n - 1)
        
        visited = set()
        burned_edges = set()
        
        self._burn_node(start_node, visited, burned_edges)
        
        # 构建子图
        node_list = sorted(list(visited))
        node_map = {node: idx for idx, node in enumerate(node_list)}
        
        subgraph = Graph(n=len(node_list), directed=self.graph.directed)
        
        for u, v in burned_edges:
            subgraph.add_edge(node_map[u], node_map[v])
        
        return subgraph


def compute_sampling_fidelity(original: Graph, sampled: Graph) -> float:
    """
    计算采样保真度
    
    参数:
        original: 原图
        sampled: 采样图
    
    返回:
        保真度分数（0-1之间）
    """
    # 简化的保真度计算：度数分布相似度
    orig_degrees = sorted(original.degrees)
    samp_degrees = sorted(sampled.degrees)
    
    # 取相同长度进行比较
    n = min(len(orig_degrees), len(samp_degrees))
    
    # 计算均方根误差
    mse = sum((orig_degrees[i] - samp_degrees[i]) ** 2 for i in range(n)) / n
    
    # 转换为保真度分数
    max_mse = sum(d ** 2 for d in orig_degrees) / n
    fidelity = 1.0 - (mse / max_mse) if max_mse > 0 else 1.0
    
    return max(0.0, min(1.0, fidelity))


if __name__ == "__main__":
    print("=== 图采样算法测试 ===")
    
    # 创建测试图
    g = Graph(n=100, directed=False)
    # 生成一个小世界网络
    for i in range(100):
        for j in range(i + 1, min(i + 6, 100)):
            if random.random() < 0.3:
                g.add_edge(i, j)
    
    print(f"原图: {g.n} 节点")
    
    # 测试 Node2Vec
    print("\n--- Node2Vec 采样 ---")
    node2vec = Node2VecSampler(g, p=1.0, q=1.0)
    walks = node2vec.sample_walks(num_walks=5, walk_length=10)
    print(f"采样 {len(walks)} 条游走路径")
    print(f"示例游走: {walks[0] if walks else 'N/A'}")
    
    # 测试 p=0.5 (倾向于BFS), q=2.0 (倾向于DFS)
    node2vec_bfs = Node2VecSampler(g, p=0.5, q=0.5)  # BFS倾向
    walks_bfs = node2vec_bfs.sample_walks(num_walks=5, walk_length=10)
    print(f"BFS倾向游走: {walks_bfs[0] if walks_bfs else 'N/A'}")
    
    # 测试 GraphSAINT
    print("\n--- GraphSAINT 采样 ---")
    saint_node = GraphSAINTSampler(g, sample_size=20, method="node")
    subg_node = saint_node.sample()
    print(f"节点采样: {subg_node.n} 节点")
    fidelity_node = compute_sampling_fidelity(g, subg_node)
    print(f"保真度: {fidelity_node:.3f}")
    
    saint_edge = GraphSAINTSampler(g, sample_size=20, method="edge")
    subg_edge = saint_edge.sample()
    print(f"边采样: {subg_edge.n} 节点")
    fidelity_edge = compute_sampling_fidelity(g, subg_edge)
    print(f"保真度: {fidelity_edge:.3f}")
    
    saint_ring = GraphSAINTSampler(g, sample_size=20, method="ring")
    subg_ring = saint_ring.sample()
    print(f"循环采样: {subg_ring.n} 节点")
    fidelity_ring = compute_sampling_fidelity(g, subg_ring)
    print(f"保真度: {fidelity_ring:.3f}")
    
    # 测试 Forest Fire
    print("\n--- Forest Fire 采样 ---")
    ff = ForestFireSampler(g, forward_prob=0.6, max_nodes=20)
    subg_ff = ff.sample()
    print(f"火灾采样: {subg_ff.n} 节点")
    fidelity_ff = compute_sampling_fidelity(g, subg_ff)
    print(f"保真度: {fidelity_ff:.3f}")
    
    print("\n=== 测试完成 ===")
