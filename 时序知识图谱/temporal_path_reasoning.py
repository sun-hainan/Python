"""
时序路径推理 (Temporal Path Reasoning)
=====================================
实现时序路径查询和推理，支持带有时间约束的路径遍历。

核心功能：
1. 时序路径查询：带时间约束的路径发现
2. 时序路径排序：基于时间一致性的排序
3. 时序路径推理：基于路径模式的推理

参考：
    - Temporal Path Queries in Knowledge Graphs.
    - TimeLine: A History-aware Query Engine.
"""

from typing import List, Dict, Set, Tuple, Optional, Any, Callable
from collections import defaultdict, deque
import heapq


class TemporalPath:
    """时序路径"""
    def __init__(self, nodes: List[str], edges: List[Tuple], 
                 times: List[Any], score: float = 0.0):
        self.nodes = nodes      # 节点序列
        self.edges = edges      # 边序列 (s, p, o)
        self.times = times      # 时间戳序列
        self.score = score      # 路径得分
        self.constraints = []  # 满足的约束
    
    def length(self) -> int:
        """路径长度（边数）"""
        return len(self.edges)
    
    def temporal_span(self) -> float:
        """时间跨度"""
        if not self.times:
            return 0.0
        return max(self.times) - min(self.times)
    
    def is_temporally_consistent(self) -> bool:
        """检查时间一致性（时间是否递增）"""
        for i in range(len(self.times) - 1):
            if self.times[i+1] < self.times[i]:
                return False
        return True
    
    def __str__(self):
        parts = []
        for i, (s, p, o) in enumerate(self.edges):
            t = self.times[i] if i < len(self.times) else "?"
            parts.append(f"{s}--[{p}]@{t}-->{o}")
        return " -> ".join(parts) + f" (score={self.score:.3f})"


class TemporalPathQueryEngine:
    """
    时序路径查询引擎
    
    参数:
        kg: 时序知识图谱
        max_length: 最大路径长度
    """
    
    def __init__(self, kg, max_length: int = 5):
        self.kg = kg
        self.max_length = max_length
    
    def find_paths(self, source: str, target: str,
                  time_range: Optional[Tuple[Any, Any]] = None,
                  relation_filter: Optional[Set[str]] = None,
                  top_k: int = 10) -> List[TemporalPath]:
        """
        找从source到target的时序路径
        
        参数:
            source: 起点
            target: 终点
            time_range: 时间范围 (start, end)
            relation_filter: 允许的关系类型
            top_k: 返回前k条
        
        返回:
            路径列表
        """
        paths = []
        
        # BFS搜索
        queue = deque([(source, [source], [], [])])
        visited = {source: 0}  # node -> earliest_arrival_time
        
        while queue:
            current, node_path, edge_path, time_path = queue.popleft()
            
            if len(edge_path) > self.max_length:
                continue
            
            # 检查是否到达目标
            if current == target and edge_path:
                path = TemporalPath(
                    nodes=node_path,
                    edges=edge_path,
                    times=time_path,
                    score=self._compute_path_score(edge_path, time_path)
                )
                paths.append(path)
                
                if len(paths) >= top_k * 2:  # 搜索更多后排序
                    break
            
            # 获取邻居
            neighbors = self.kg.get_temporal_neighbors(current)
            
            for neighbor, relation, time in neighbors:
                # 关系过滤
                if relation_filter and relation not in relation_filter:
                    continue
                
                # 时间范围过滤
                if time_range:
                    t_start, t_end = time_range
                    if isinstance(time, tuple):
                        time_start, time_end = time
                    else:
                        time_start = time_end = time
                    
                    # 路径时间约束：下一跳必须在上一跳之后
                    if time_start < (time_path[-1] if time_path else t_start - 1):
                        continue
                
                if neighbor not in visited or len(node_path) < visited[neighbor]:
                    new_node_path = node_path + [neighbor]
                    new_edge_path = edge_path + [(current, relation, neighbor)]
                    new_time_path = time_path + [time]
                    
                    visited[neighbor] = len(new_node_path)
                    queue.append((neighbor, new_node_path, new_edge_path, new_time_path))
        
        # 排序并返回top_k
        paths.sort(key=lambda p: p.score, reverse=True)
        return paths[:top_k]
    
    def _compute_path_score(self, edges: List[Tuple], times: List[Any]) -> float:
        """
        计算路径得分
        
        参数:
            edges: 边列表
            times: 时间列表
        
        返回:
            得分
        """
        # 因素：
        # 1. 路径长度（越短越好）
        # 2. 时间一致性（时间递增）
        # 3. 时间跨度（越小可能越精确）
        
        length_score = 1.0 / (1.0 + len(edges))
        
        # 时间一致性
        consistency_score = 1.0
        for i in range(len(times) - 1):
            if times[i+1] < times[i]:
                consistency_score *= 0.5
        
        # 时间跨度
        if len(times) > 1:
            span = max(times) - min(times)
            span_score = 1.0 / (1.0 + span * 0.01)
        else:
            span_score = 1.0
        
        return length_score * consistency_score * span_score
    
    def find_temporal_shortest_path(self, source: str, target: str,
                                   time_constraint: Optional[Any] = None) -> Optional[TemporalPath]:
        """
        找最短时序路径（带时间约束的最短路径）
        
        参数:
            source: 起点
            target: 终点
            time_constraint: 时间约束
        
        返回:
            最短路径或None
        """
        # Dijkstra变体
        dist = {source: 0}
        parent = {source: (None, None, None)}  # (prev_node, relation, time)
        pq = [(0, source)]
        
        while pq:
            d, current = heapq.heappop(pq)
            
            if d > dist.get(current, float('inf')):
                continue
            
            if current == target:
                # 重构路径
                return self._reconstruct_path(parent, source, target)
            
            neighbors = self.kg.get_temporal_neighbors(current)
            
            for neighbor, relation, time in neighbors:
                # 时间约束检查
                if time_constraint is not None:
                    if isinstance(time, tuple):
                        if time[0] < time_constraint:
                            continue
                    elif time < time_constraint:
                        continue
                
                # 权重：边代价 + 时间代价
                edge_cost = 1.0
                time_cost = 0.0 if not time_path else max(0, time - last_time)
                
                new_dist = d + edge_cost + time_cost * 0.1
                
                if new_dist < dist.get(neighbor, float('inf')):
                    dist[neighbor] = new_dist
                    parent[neighbor] = (current, relation, time)
                    heapq.heappush(pq, (new_dist, neighbor))
        
        return None
    
    def _reconstruct_path(self, parent: Dict, source: str, target: str) -> TemporalPath:
        """重构路径"""
        nodes = []
        edges = []
        times = []
        
        current = target
        while current is not None:
            nodes.append(current)
            if current in parent and parent[current][0] is not None:
                prev, relation, time = parent[current]
                edges.append((prev, relation, current))
                times.append(time)
            else:
                break
            current = prev
        
        nodes.reverse()
        edges.reverse()
        times.reverse()
        
        return TemporalPath(nodes, edges, times, score=0.0)


class TemporalPathPattern:
    """时序路径模式"""
    
    def __init__(self):
        self.patterns = defaultdict(int)
        self.temporal_patterns = defaultdict(int)
    
    def mine_patterns(self, kg, min_support: int = 2) -> Dict[Tuple, int]:
        """
        挖掘频繁时序路径模式
        
        参数:
            kg: 时序知识图谱
            min_support: 最小支持度
        
        返回:
            模式字典
        """
        # 获取所有路径
        entities = list(kg.entities)
        
        engine = TemporalPathQueryEngine(kg, max_length=3)
        
        for source in entities:
            for target in entities:
                if source != target:
                    paths = engine.find_paths(source, target, top_k=20)
                    for path in paths:
                        # 提取边模式
                        edge_pattern = tuple(e[1] for e in path.edges)
                        self.patterns[edge_pattern] += 1
                        
                        # 提取时序模式
                        if path.is_temporally_consistent():
                            time_pattern = tuple(path.times)
                            self.temporal_patterns[time_pattern] += 1
        
        # 过滤低频
        return {
            k: v for k, v in self.patterns.items()
            if v >= min_support
        }
    
    def get_sequence_pattern(self, path: TemporalPath) -> str:
        """获取路径的序列模式表示"""
        parts = []
        for i, (s, p, o) in enumerate(path.edges):
            t = path.times[i]
            parts.append(f"{p}@{t}")
        return " -> ".join(parts)


class TemporalConstraintReasoner:
    """
    时序约束推理器
    
    支持：
    - 时间顺序约束
    - 时间范围约束
    - 时间距离约束
    """
    
    def __init__(self, kg):
        self.kg = kg
        self.constraints = []
    
    def add_constraint(self, constraint_type: str, 
                     entities: List[str], temporal_bounds: Tuple):
        """
        添加时序约束
        
        参数:
            constraint_type: 约束类型 ("before", "after", "between", "distance")
            entities: 涉及的实体
            temporal_bounds: 时间边界
        """
        self.constraints.append({
            "type": constraint_type,
            "entities": entities,
            "bounds": temporal_bounds
        })
    
    def check_constraint(self, path: TemporalPath) -> bool:
        """
        检查路径是否满足约束
        
        参数:
            path: 时序路径
        
        返回:
            是否满足
        """
        for constraint in self.constraints:
            ctype = constraint["type"]
            entities = constraint["entities"]
            bounds = constraint["bounds"]
            
            if ctype == "before":
                # 检查before关系
                for i, (s, p, o) in enumerate(path.edges):
                    t = path.times[i]
                    if t > bounds[1]:
                        return False
            
            elif ctype == "between":
                # 检查时间范围
                for i, t in enumerate(path.times):
                    if not (bounds[0] <= t <= bounds[1]):
                        return False
        
        return True
    
    def infer_missing_time(self, s: str, p: str, o: str,
                          lower_bound: Any, upper_bound: Any) -> Optional[Any]:
        """
        推断缺失的时间
        
        参数:
            s, p, o: 三元组
            lower_bound: 下界
            upper_bound: 上界
        
        返回:
            推断的时间或None
        """
        # 检查是否有相关信息可以推断
        # 简化：返回中点
        return (lower_bound + upper_bound) / 2


if __name__ == "__main__":
    print("=== 时序路径推理测试 ===")
    
    from temporal_knowledge_graph import TemporalKG
    
    # 构建测试TKG
    kg = TemporalKG()
    
    facts = [
        ("Alice", "works_at", "CompanyA", 2018),
        ("CompanyA", "located_in", "Paris", 2018),
        ("Alice", "moved_to", "London", 2020),
        ("CompanyA", "acquired", "CompanyB", 2019),
        ("CompanyB", "located_in", "NYC", 2019),
        ("Alice", "married_to", "Bob", 2019),
        ("Bob", "works_at", "CompanyB", 2020),
    ]
    
    for s, p, o, t in facts:
        kg.add_triple(s, p, o, t)
    
    # 创建路径查询引擎
    engine = TemporalPathQueryEngine(kg, max_length=4)
    
    # 查询路径
    print("\n--- 时序路径查询 ---")
    
    paths = engine.find_paths("Alice", "Paris", time_range=(2015, 2025), top_k=5)
    print(f"\nAlice到Paris的路径:")
    for i, path in enumerate(paths):
        print(f"  路径{i+1}: {path}")
    
    # 查询另一条路径
    paths2 = engine.find_paths("Alice", "CompanyB", top_k=5)
    print(f"\nAlice到CompanyB的路径:")
    for i, path in enumerate(paths2):
        print(f"  路径{i+1}: {path}")
        print(f"    时间一致性: {'是' if path.is_temporally_consistent() else '否'}")
        print(f"    时间跨度: {path.temporal_span()}")
    
    # 最短时序路径
    print("\n--- 最短时序路径 ---")
    shortest = engine.find_temporal_shortest_path("Alice", "NYC")
    if shortest:
        print(f"Alice到NYC的最短路径: {shortest}")
    
    # 路径模式挖掘
    print("\n--- 路径模式挖掘 ---")
    pattern_miner = TemporalPathPattern()
    patterns = pattern_miner.mine_patterns(kg, min_support=1)
    print(f"发现 {len(patterns)} 种模式:")
    for pattern, count in list(patterns.items())[:5]:
        print(f"  {pattern}: {count}")
    
    # 时序约束推理
    print("\n--- 时序约束推理 ---")
    reasoner = TemporalConstraintReasoner(kg)
    
    # 添加约束
    reasoner.add_constraint("between", ["Alice", "Paris"], (2015, 2022))
    
    # 检查路径
    for path in paths[:1]:
        satisfies = reasoner.check_constraint(path)
        print(f"路径满足约束: {satisfies}")
    
    print("\n=== 测试完成 ===")
