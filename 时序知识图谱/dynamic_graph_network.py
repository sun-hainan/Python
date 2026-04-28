"""
动态图网络 (Dynamic Graph Networks)
==================================
实现动态图的时序演变建模和增量更新。

核心概念：
- 动态图：节点和边随时间变化的图
- 时间片快照：离散时间点的图快照序列
- 增量更新：高效更新图结构

支持的模型：
1. 基于快照的方法
2. 基于事件流的方法
3. 时序邻居聚合

参考：
    - Kumar, S. et al. (2019). FastGraph: Efficient Graph Learning.
    - Zhou, L. et al. (2018). Dynamic Graph Representation Learning.
"""

from typing import List, Dict, Set, Tuple, Optional, Any, Callable
from collections import defaultdict, deque
import copy


class DynamicNode:
    """动态节点"""
    def __init__(self, node_id: str, attributes: Optional[Dict] = None):
        self.id = node_id
        self.attributes = attributes or {}
        self.timestamps = []  # 节点活跃的时间点
        self.embeddings = {}  # time -> embedding
    
    def add_timestamp(self, t: Any):
        """记录节点活跃时间"""
        if t not in self.timestamps:
            self.timestamps.append(t)
            self.timestamps.sort()


class DynamicEdge:
    """动态边"""
    def __init__(self, source: str, target: str, weight: float = 1.0,
                 start_time: Any = None, end_time: Any = None):
        self.source = source
        self.target = target
        self.weight = weight
        self.start_time = start_time
        self.end_time = end_time if end_time else start_time
    
    def is_active(self, time: Any) -> bool:
        """检查边在给定时间是否活跃"""
        if self.start_time is None:
            return True
        if self.end_time is None:
            return self.start_time <= time
        return self.start_time <= time <= self.end_time


class DynamicGraph:
    """
    动态图
    
    支持多种表示方式：
    - 快照序列
    - 边事件流
    - 时序邻接表
    """
    
    def __init__(self, name: str = "DynamicGraph"):
        self.name = name
        self.nodes = {}  # node_id -> DynamicNode
        self.edges = []  # 边事件列表 (source, target, time, weight)
        self.time_snapshots = {}  # time -> Graph snapshot
        self.sorted_times = []  # 时间点排序列表
    
    def add_node(self, node_id: str, t: Any, attributes: Optional[Dict] = None):
        """添加节点"""
        if node_id not in self.nodes:
            self.nodes[node_id] = DynamicNode(node_id, attributes)
        self.nodes[node_id].add_timestamp(t)
    
    def add_edge(self, source: str, target: str, t: Any, weight: float = 1.0):
        """添加边事件"""
        self.edges.append((source, target, t, weight))
        
        # 确保节点存在
        self.add_node(source, t)
        self.add_node(target, t)
        
        # 更新排序时间
        if t not in self.time_snapshots:
            self.time_snapshots[t] = None  # 延迟构建
            self.sorted_times.append(t)
            self.sorted_times.sort()
    
    def get_snapshot(self, t: Any) -> 'Graph':
        """
        获取时间点t的图快照
        
        参数:
            t: 时间点
        
        返回:
            快照图
        """
        from graph_sampling_algorithms import Graph
        
        # 收集到时间t为止的边
        edges_at_t = []
        for s, tgt, time, w in self.edges:
            if time <= t:
                edges_at_t.append((s, tgt, w))
        
        # 构建图
        g = Graph(len(self.nodes))
        for s, tgt, w in edges_at_t:
            g.add_edge(s, tgt)
        
        return g
    
    def get_temporal_neighbors(self, node: str, t: Any, 
                              window: Optional[int] = None) -> Set[Tuple[str, Any]]:
        """
        获取节点在时间t的时序邻居
        
        参数:
            node: 节点
            t: 时间点
            window: 时间窗口大小
        
        返回:
            {(邻居, 时间), ...}
        """
        neighbors = set()
        
        for s, tgt, time, w in self.edges:
            if s == node and time <= t:
                neighbors.add((tgt, time))
            elif tgt == node and time <= t:
                neighbors.add((s, time))
        
        return neighbors
    
    def evolve_to(self, t: Any) -> 'DynamicGraph':
        """
        获取到时间t为止的子图
        
        参数:
            t: 目标时间
        
        返回:
            动态子图
        """
        subgraph = DynamicGraph(f"{self.name}_to_{t}")
        
        # 添加边
        for s, tgt, time, w in self.edges:
            if time <= t:
                subgraph.add_edge(s, tgt, time, w)
        
        return subgraph


class IncrementalGraphUpdate:
    """
    增量图更新算法
    
    支持高效的边插入和删除操作
    """
    
    def __init__(self, graph: DynamicGraph):
        self.graph = graph
        self.adj = defaultdict(set)  # 邻接表
        self.edge_weights = {}  # (s, t) -> weight
    
    def insert_edge(self, source: str, target: str, t: Any, weight: float = 1.0):
        """
        插入边
        
        参数:
            source: 源节点
            target: 目标节点
            t: 时间
            weight: 权重
        """
        self.adj[source].add(target)
        self.adj[target].add(source)
        self.edge_weights[(source, target)] = weight
        self.graph.add_edge(source, target, t, weight)
    
    def delete_edge(self, source: str, target: str):
        """删除边"""
        if target in self.adj[source]:
            self.adj[source].discard(target)
            self.adj[target].discard(source)
            key = (source, target)
            if key in self.edge_weights:
                del self.edge_weights[key]
    
    def get_neighbors(self, node: str, t: Optional[Any] = None) -> Set[str]:
        """获取邻居节点"""
        if t is None:
            return self.adj.get(node, set())
        
        neighbors = set()
        for neighbor in self.adj.get(node, set()):
            key = (min(node, neighbor), max(node, neighbor))
            edge_time = self._get_edge_time(key)
            if edge_time and edge_time <= t:
                neighbors.add(neighbor)
        
        return neighbors
    
    def _get_edge_time(self, edge_key: Tuple) -> Optional[Any]:
        """获取边的时间戳"""
        for s, t, time, w in self.graph.edges:
            key = (min(s, t), max(s, t))
            if key == edge_key:
                return time
        return None


class TemporalNeighborAggregator:
    """
    时序邻居聚合器
    
    用于在动态图上进行邻居信息聚合
    """
    
    def __init__(self, graph: DynamicGraph, embedding_dim: int = 64):
        self.graph = graph
        self.embedding_dim = embedding_dim
        self.node_embeddings = {}
    
    def aggregate(self, node: str, t: Any, 
                 num_hops: int = 2) -> List[float]:
        """
        聚合节点在时间t的时序邻居信息
        
        参数:
            node: 节点
            t: 时间点
            num_hops: 聚合跳数
        
        返回:
            聚合嵌入向量
        """
        import random
        random.seed(42)
        
        # 初始化（如果不存在）
        if node not in self.node_embeddings:
            self.node_embeddings[node] = [
                random.gauss(0, 0.1) for _ in range(self.embedding_dim)
            ]
        
        # 获取时序邻居
        neighbors = self.graph.get_temporal_neighbors(node, t)
        
        # 简单聚合：平均
        if not neighbors:
            return self.node_embeddings[node]
        
        aggregated = [0.0] * self.embedding_dim
        
        for neighbor, time in neighbors:
            if neighbor in self.node_embeddings:
                neighbor_emb = self.node_embeddings[neighbor]
                # 时间衰减
                time_diff = abs(t - time) if isinstance(time, (int, float)) else 1
                decay = 1.0 / (1.0 + time_diff)
                
                for i in range(self.embedding_dim):
                    aggregated[i] += neighbor_emb[i] * decay
        
        # 归一化
        n = len(neighbors)
        aggregated = [x / n for x in aggregated]
        
        return aggregated
    
    def update_embeddings(self, t: Any, learning_rate: float = 0.01):
        """
        更新节点嵌入
        
        参数:
            t: 当前时间
            learning_rate: 学习率
        """
        for node in self.graph.nodes:
            self.aggregate(node, t)


class DynamicGraphEncoder:
    """
    动态图编码器
    
    将动态图编码为向量表示
    """
    
    def __init__(self, graph: DynamicGraph, embedding_dim: int = 64):
        self.graph = graph
        self.embedding_dim = embedding_dim
        self.time_embeddings = {}
        self.node_embeddings = {}
    
    def encode_at_time(self, t: Any) -> Dict[str, List[float]]:
        """
        编码时间点t的图
        
        参数:
            t: 时间点
        
        返回:
            node -> embedding 的字典
        """
        import random
        random.seed(hash(t) % 1000000)
        
        snapshot = self.graph.get_snapshot(t)
        
        # 简单编码：基于节点度数
        embeddings = {}
        for node in snapshot.nodes:
            degree = snapshot.degree(node)
            emb = [random.gauss(0, 0.1) * (degree + 1) for _ in range(self.embedding_dim)]
            embeddings[node] = emb
        
        return embeddings
    
    def compute_temporal_similarity(self, node: str, t1: Any, t2: Any) -> float:
        """
        计算节点在不同时刻表示的相似度
        
        参数:
            node: 节点
            t1: 时间1
            t2: 时间2
        
        返回:
            余弦相似度
        """
        emb1 = self.encode_at_time(t1).get(node, [0] * self.embedding_dim)
        emb2 = self.encode_at_time(t2).get(node, [0] * self.embedding_dim)
        
        # 余弦相似度
        dot = sum(a * b for a, b in zip(emb1, emb2))
        norm1 = sum(a * a for a in emb1) ** 0.5
        norm2 = sum(a * a for a in emb2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot / (norm1 * norm2)


def detect_change_points(graph: DynamicGraph, metric: str = "edge_count") -> List[Any]:
    """
    检测动态图的变点（结构发生显著变化的时间点）
    
    参数:
        graph: 动态图
        metric: 衡量指标 ("edge_count", "degree_distribution")
    
    返回:
        变点时间列表
    """
    change_points = []
    
    times = graph.sorted_times
    if len(times) < 2:
        return []
    
    # 计算每个时间点的指标
    values = []
    for t in times:
        snapshot = graph.get_snapshot(t)
        
        if metric == "edge_count":
            m = sum(1 for _ in snapshot.nodes)  # 简化
            values.append(len(graph.edges))
        else:
            values.append(len(graph.nodes))
    
    # 检测显著变化
    for i in range(1, len(values)):
        diff = abs(values[i] - values[i-1])
        avg = sum(values[:i]) / i if i > 0 else values[0]
        
        if avg > 0 and diff / avg > 0.5:  # 50%变化阈值
            change_points.append(times[i])
    
    return change_points


if __name__ == "__main__":
    print("=== 动态图网络测试 ===")
    
    # 创建动态图
    dg = DynamicGraph("TestDynamicGraph")
    
    # 添加边事件
    events = [
        ("A", "B", 2020, 1.0),
        ("B", "C", 2020, 1.0),
        ("A", "C", 2021, 1.0),
        ("C", "D", 2022, 1.0),
        ("A", "D", 2022, 1.0),
        ("B", "D", 2023, 1.0),
    ]
    
    for s, t, time, w in events:
        dg.add_edge(s, t, time, w)
    
    print(f"动态图: {len(dg.nodes)} 节点, {len(dg.edges)} 边事件")
    print(f"时间点: {dg.sorted_times}")
    
    # 获取快照
    print("\n--- 图快照 ---")
    snapshot_2020 = dg.get_snapshot(2020)
    print(f"2020年快照: {snapshot_2020.n} 节点")
    
    snapshot_2022 = dg.get_snapshot(2022)
    print(f"2022年快照: {snapshot_2022.n} 节点")
    
    # 时序邻居
    print("\n--- 时序邻居 ---")
    neighbors_2020 = dg.get_temporal_neighbors("A", 2020)
    print(f"A在2020年的时序邻居: {neighbors_2020}")
    
    neighbors_2022 = dg.get_temporal_neighbors("A", 2022)
    print(f"A在2022年的时序邻居: {neighbors_2022}")
    
    # 增量更新
    print("\n--- 增量更新 ---")
    updater = IncrementalGraphUpdate(dg)
    updater.insert_edge("E", "F", 2024, 1.0)
    print(f"插入边 (E, F) at 2024")
    
    neighbors = updater.get_neighbors("A", 2024)
    print(f"A在2024年的邻居: {neighbors}")
    
    # 时序邻居聚合
    print("\n--- 时序邻居聚合 ---")
    aggregator = TemporalNeighborAggregator(dg, embedding_dim=8)
    
    emb_A_2020 = aggregator.aggregate("A", 2020)
    print(f"A在2020年的聚合嵌入: {[f'{x:.3f}' for x in emb_A_2020]}")
    
    emb_A_2022 = aggregator.aggregate("A", 2022)
    print(f"A在2022年的聚合嵌入: {[f'{x:.3f}' for x in emb_A_2022]}")
    
    # 动态图编码
    print("\n--- 动态图编码 ---")
    encoder = DynamicGraphEncoder(dg, embedding_dim=8)
    
    emb_at_2020 = encoder.encode_at_time(2020)
    emb_at_2022 = encoder.encode_at_time(2022)
    
    print(f"2020年编码: A={[f'{x:.2f}' for x in emb_at_2020.get('A', [])]}")
    print(f"2022年编码: A={[f'{x:.2f}' for x in emb_at_2022.get('A', [])]}")
    
    # 变点检测
    print("\n--- 变点检测 ---")
    change_points = detect_change_points(dg)
    print(f"检测到的变点: {change_points}")
    
    print("\n=== 测试完成 ===")
