# -*- coding: utf-8 -*-
"""
算法实现：06_网络流与匹配 / multi_commodity_flow

本文件实现 multi_commodity_flow 相关的算法功能。
"""

from collections import defaultdict
import itertools


class MultiCommodityFlow:
    """多商品流问题"""
    
    def __init__(self, n):
        self.n = n  # 节点数
        self.commodities = []  # [(s_i, t_i, d_i), ...]
        self.capacity = {}  # (u, v) -> capacity
        self.graph = defaultdict(list)
    
    def add_edge(self, u, v, cap):
        """添加一条边及其容量"""
        self.capacity[(u, v)] = cap
        self.capacity[(v, u)] = cap  # 无向
        self.graph[u].append(v)
        self.graph[v].append(u)
    
    def add_commodity(self, source, sink, demand):
        """添加一个商品（源、汇、需求）"""
        self.commodities.append((source, sink, demand))
    
    def greedy_routing(self):
        """
        贪婪路由算法（近似算法）
        
        思想：按需求从大到小处理每个商品
        每次用最大流找最短路（按跳数）
        
        返回：各商品的路由路径
        """
        # 按需求排序（从大到小）
        sorted_comms = sorted(self.commodities, key=lambda x: -x[2])
        
        # 剩余容量
        residual = dict(self.capacity)
        
        # 存储每个商品的路径
        routes = {}
        
        for idx, (s, t, d) in enumerate(sorted_comms):
            path = self._shortest_path_bfs(s, t, residual)
            
            if not path:
                print(f"  商品 {idx}: 无法找到路由！")
                routes[idx] = []
                continue
            
            # 沿路径发送流量（取路径容量和需求的最小值）
            path_cap = min(d, min(residual.get((path[i], path[i+1]), 0) 
                                   for i in range(len(path)-1)))
            
            # 更新剩余容量
            for i in range(len(path)-1):
                u, v = path[i], path[i+1]
                residual[(u, v)] -= path_cap
                residual[(v, u)] -= path_cap
            
            routes[idx] = {'path': path, 'flow': path_cap, 
                          's': s, 't': t, 'd': d}
            
            print(f"  商品 {idx}: {s}->{t}, 需求{d}, 实际流量{path_cap}, 路径{[p for p in path]}")
        
        return routes
    
    def _shortest_path_bfs(self, source, sink, residual):
        """BFS 找最短路（按跳数）"""
        from collections import deque
        
        parent = {source: None}
        queue = deque([source])
        
        while queue:
            u = queue.popleft()
            if u == sink:
                break
            for v in self.graph[u]:
                if v not in parent:
                    edge_cap = residual.get((u, v), 0)
                    if edge_cap > 0:
                        parent[v] = u
                        queue.append(v)
        
        if sink not in parent:
            return None
        
        # 重建路径
        path = []
        v = sink
        while v is not None:
            path.append(v)
            v = parent[v]
        path.reverse()
        
        return path
    
    def fractional_lp_relaxation(self):
        """
        LP 松弛的简化版本
        实际应用中应使用 scipy 或 CVXPY
        
        这里演示概念：
        min 0
        s.t. sum_k f_e^k <= cap_e  for all e
             sum_e f_e^k = d_k    for all k (流量守恒)
             f_e^k >= 0
        """
        print("\nLP 松弛（简化说明）：")
        print("  变量: f_e^k = 商品 k 在边 e 上的流量")
        print("  约束1: 对于每条边 e，sum_k f_e^k <= cap_e（容量约束）")
        print("  约束2: 对于每个商品 k，流量守恒")
        print("  约束3: f_e^k >= 0")
        print("\n  实际求解应使用线性规划求解器（如 scipy, CVXPY）")


def build_multi_commodity_example():
    """构建多商品流示例"""
    n = 6
    mcf = MultiCommodityFlow(n)
    
    # 添加边（无向）
    edges = [(0, 1, 5), (0, 2, 4), (1, 2, 2), (1, 3, 4), 
             (2, 3, 3), (2, 4, 4), (3, 5, 5), (4, 5, 3)]
    for u, v, cap in edges:
        mcf.add_edge(u, v, cap)
    
    # 添加商品
    mcf.add_commodity(0, 5, 3)  # 商品0: 0->5, 需求3
    mcf.add_commodity(0, 3, 2)  # 商品1: 0->3, 需求2
    mcf.add_commodity(2, 5, 2)  # 商品2: 2->5, 需求2
    
    return mcf


if __name__ == "__main__":
    print("=" * 55)
    print("多商品流（Multi-Commodity Flow）")
    print("=" * 55)
    
    mcf = build_multi_commodity_example()
    
    print(f"\n网络：{mcf.n} 节点")
    print("\n边及容量：")
    shown = set()
    for (u, v), cap in mcf.capacity.items():
        if u < v:
            print(f"  ({u}, {v}): {cap}")
            shown.add((u, v))
    
    print("\n商品列表：")
    for i, (s, t, d) in enumerate(mcf.commodities):
        print(f"  商品 {i}: {s} -> {t}, 需求 = {d}")
    
    print("\n贪婪路由执行：")
    routes = mcf.greedy_routing()
    
    total_flow = sum(r.get('flow', 0) for r in routes.values())
    total_demand = sum(d for _, _, d in mcf.commodities)
    
    print(f"\n结果：总流量 {total_flow}/{total_demand}")
    print(f"需求满足率: {100*total_flow/total_demand:.1f}%")
    
    mcf.fractional_lp_relaxation()
