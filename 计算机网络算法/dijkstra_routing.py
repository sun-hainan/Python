# -*- coding: utf-8 -*-
"""
算法实现：计算机网络算法 / dijkstra_routing

本文件实现 dijkstra_routing 相关的算法功能。
"""

import heapq
import math


class Graph:
    """加权有向图"""

    def __init__(self):
        """初始化空图"""
        # 邻接表：{vertex: [(neighbor, weight), ...]}
        self.adjacency = {}
        # 边列表（用于迭代）
        self.edges = []

    def add_vertex(self, v):
        """
        添加顶点
        
        参数:
            v: 顶点标识
        """
        if v not in self.adjacency:
            self.adjacency[v] = []

    def add_edge(self, u, v, weight):
        """
        添加边
        
        参数:
            u: 起点
            v: 终点
            weight: 权重（必须为非负数）
        """
        self.add_vertex(u)
        self.add_vertex(v)
        self.adjacency[u].append((v, weight))
        self.edges.append((u, v, weight))

    def add_undirected_edge(self, u, v, weight):
        """
        添加无向边（双向）
        
        参数:
            u: 端点1
            v: 端点2
            weight: 权重
        """
        self.add_edge(u, v, weight)
        self.add_edge(v, u, weight)

    def get_neighbors(self, v):
        """获取顶点的邻居"""
        return self.adjacency.get(v, [])

    def vertices(self):
        """返回所有顶点"""
        return list(self.adjacency.keys())

    def __len__(self):
        """返回顶点数"""
        return len(self.adjacency)


class DijkstraRouter:
    """基于 Dijkstra 的路由计算器"""

    def __init__(self, graph):
        """
        初始化路由器
        
        参数:
            graph: Graph 对象
        """
        self.graph = graph
        # 距离表：{source: {dest: (distance, path)}}
        self.routing_tables = {}

    def compute_shortest_path(self, source):
        """
        计算从源点到所有其他顶点的最短路径
        
        参数:
            source: 源点标识
        返回:
            distances: {dest: distance} 距离字典
            predecessors: {dest: prev_vertex} 前驱字典
        """
        distances = {source: 0}
        predecessors = {source: None}
        
        # 优先队列：(distance, vertex)
        pq = [(0, source)]
        # 已访问顶点集合
        visited = set()
        
        while pq:
            # 取出最小距离的顶点
            dist, u = heapq.heappop(pq)
            
            if u in visited:
                continue
            
            visited.add(u)
            
            # 遍历邻居
            for v, weight in self.graph.get_neighbors(u):
                if v in visited:
                    continue
                
                new_dist = dist + weight
                
                # 如果发现更短的路径
                if v not in distances or new_dist < distances[v]:
                    distances[v] = new_dist
                    predecessors[v] = u
                    heapq.heappush(pq, (new_dist, v))
        
        return distances, predecessors

    def compute_all_pairs_shortest_path(self):
        """
        计算所有顶点对之间的最短路径
        
        为每个顶点运行一次 Dijkstra
        """
        self.routing_tables = {}
        
        for vertex in self.graph.vertices():
            distances, predecessors = self.compute_shortest_path(vertex)
            self.routing_tables[vertex] = {
                'distances': distances,
                'predecessors': predecessors
            }

    def get_route(self, source, destination):
        """
        获取从源点到目的地的路由
        
        参数:
            source: 源点
            destination: 目的地
        返回:
            (path, distance): 路径列表和距离
        """
        if source not in self.routing_tables:
            self.compute_shortest_path(source)
        
        table = self.routing_tables.get(source, {})
        if not table:
            return None, float('inf')
        
        distances = table.get('distances', {})
        predecessors = table.get('predecessors', {})
        
        if destination not in distances:
            return None, float('inf')
        
        # 重建路径
        path = []
        current = destination
        while current is not None:
            path.append(current)
            current = predecessors.get(current)
        
        path.reverse()
        
        return path, distances[destination]

    def get_next_hop(self, source, destination):
        """
        获取到目的地的下一跳
        
        参数:
            source: 源点
            destination: 目的地
        返回:
            next_hop: 下一跳顶点
        """
        path, _ = self.get_route(source, destination)
        if path and len(path) > 1:
            return path[1]
        return None


class NetworkTopology:
    """网络拓扑示例"""

    def __init__(self):
        """初始化网络拓扑"""
        self.graph = Graph()
        self.router_names = {}

    def add_router(self, name, router_id):
        """
        添加路由器
        
        参数:
            name: 路由器名称
            router_id: 路由器 ID
        """
        self.router_names[router_id] = name
        self.graph.add_vertex(router_id)

    def add_link(self, router1, router2, bandwidth_mbps=1000, delay_ms=1):
        """
        添加链路
        
        参数:
            router1: 路由器1 ID
            router2: 路由器2 ID
            bandwidth_mbps: 带宽（Mbps）
            delay_ms: 延迟（毫秒）
        """
        # 简化：使用延迟作为权重
        # 实际应考虑带宽、负载等因素
        weight = delay_ms
        self.graph.add_undirected_edge(router1, router2, weight)

    def compute_routing_table(self, router_id):
        """
        计算指定路由器的路由表
        
        参数:
            router_id: 路由器 ID
        返回:
            routing_table: 路由表字典
        """
        router = DijkstraRouter(self.graph)
        distances, predecessors = router.compute_shortest_path(router_id)
        
        routing_table = {}
        for dest in self.graph.vertices():
            if dest == router_id:
                continue
            
            # 重建路径
            path = []
            current = dest
            while current is not None:
                path.append(current)
                current = predecessors.get(current)
            path.reverse()
            
            routing_table[dest] = {
                'next_hop': path[1] if len(path) > 1 else None,
                'distance': distances.get(dest, float('inf')),
                'path': path
            }
        
        return routing_table

    def get_router_name(self, router_id):
        """获取路由器名称"""
        return self.router_names.get(router_id, router_id)


def build_sample_topology():
    """
    构建示例网络拓扑
    
    拓扑结构：
    A ---(10ms)--- B ---(10ms)--- C
    |              |              |
    5ms            5ms            5ms
    |              |              |
    D ---(10ms)--- E ---(10ms)--- F
    
    返回:
        topology: NetworkTopology 对象
    """
    topology = NetworkTopology()
    
    # 添加路由器
    routers = ['A', 'B', 'C', 'D', 'E', 'F']
    for r in routers:
        topology.add_router(r, r)
    
    # 添加链路
    # A-B, B-C, D-E, E-F (主干)
    topology.add_link('A', 'B', delay_ms=10)
    topology.add_link('B', 'C', delay_ms=10)
    topology.add_link('D', 'E', delay_ms=10)
    topology.add_link('E', 'F', delay_ms=10)
    
    # A-D, B-E, C-F (边缘)
    topology.add_link('A', 'D', delay_ms=5)
    topology.add_link('B', 'E', delay_ms=5)
    topology.add_link('C', 'F', delay_ms=5)
    
    return topology


if __name__ == "__main__":
    # 测试 Dijkstra 算法
    print("=== Dijkstra 最短路径算法测试 ===\n")

    # 构建示例网络
    topology = build_sample_topology()

    # 计算路由器 A 的路由表
    print("--- 路由器 A 的路由表 ---")
    routing_table = topology.compute_routing_table('A')
    
    for dest, info in routing_table.items():
        path_names = [topology.get_router_name(n) for n in info['path']]
        print(f"  -> {dest} ({topology.get_router_name(dest)}): "
              f"下一跳={info['next_hop']}, 距离={info['distance']}ms, "
              f"路径={' -> '.join(path_names)}")

    # 验证特定路径
    print("\n--- 路径验证 ---")
    router = DijkstraRouter(topology.graph)
    
    test_routes = [
        ('A', 'F'),  # A -> D -> E -> F
        ('A', 'C'),  # A -> B -> C
        ('D', 'C'),  # D -> E -> B -> C
    ]
    
    for source, dest in test_routes:
        path, distance = router.get_route(source, dest)
        path_str = ' -> '.join(path) if path else "无路径"
        print(f"  {source} -> {dest}: 距离={distance}ms, 路径={path_str}")

    # 测试全源最短路径
    print("\n--- 所有顶点对最短路径 ---")
    router.compute_all_pairs_shortest_path()
    
    print("  距离矩阵:")
    vertices = list(topology.graph.vertices())
    print("    ", "  ".join(f"{v:>4}" for v in vertices))
    
    for v1 in vertices:
        row = []
        for v2 in vertices:
            dist = router.routing_tables[v1]['distances'].get(v2, 999)
            row.append(f"{dist:>4}" if dist != 999 else "  -")
        print(f"  {v1}: " + "  ".join(row))

    # 性能测试
    print("\n--- 性能测试 ---")
    import time
    
    # 创建大型网络
    large_graph = Graph()
    num_vertices = 100
    num_edges = 500
    
    # 生成随机图
    import random
    random.seed(42)
    
    for i in range(num_vertices):
        large_graph.add_vertex(f"router_{i}")
    
    for _ in range(num_edges):
        u = f"router_{random.randint(0, num_vertices-1)}"
        v = f"router_{random.randint(0, num_vertices-1)}"
        weight = random.randint(1, 100)
        large_graph.add_edge(u, v, weight)
    
    # 计时
    large_router = DijkstraRouter(large_graph)
    
    start = time.time()
    distances, _ = large_router.compute_shortest_path('router_0')
    elapsed = time.time() - start
    
    reachable = sum(1 for d in distances.values() if d < float('inf'))
    print(f"  顶点数: {num_vertices}, 边数: {num_edges}")
    print(f"  可达顶点: {reachable}/{num_vertices}")
    print(f"  计算时间: {elapsed*1000:.2f}ms")
