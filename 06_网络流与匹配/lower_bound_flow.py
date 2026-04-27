# -*- coding: utf-8 -*-
"""
算法实现：06_网络流与匹配 / lower_bound_flow

本文件实现 lower_bound_flow 相关的算法功能。
"""

from collections import defaultdict, deque


class LowerBoundFlow:
    """上下界网络流"""
    
    def __init__(self, n, source, sink):
        self.n = n
        self.source = source
        self.sink = sink
        
        # 下界和上界
        self.lower = {}  # (u, v) -> lower_bound
        self.upper = {}  # (u, v) -> upper_bound
        
        # 邻接表（用于可行流检测）
        self.graph = defaultdict(list)
        self.capacity = {}  # (u, v) -> capacity
        self.flow = {}  # (u, v) -> current flow
    
    def add_edge(self, u, v, lower, upper):
        """添加一条有上下界的边"""
        self.lower[(u, v)] = lower
        self.upper[(u, v)] = upper
        
        # 初始化流量为 lower
        self.flow[(u, v)] = lower
        self.flow[(v, u)] = -lower
    
    def check_feasible_flow(self):
        """
        检查是否存在可行流
        
        返回：(feasible, flow_dict)
        """
        # 构造辅助网络
        n_prime = self.n + 2  # 加上附加源 s' 和附加汇 t'
        super_source = self.n
        super_sink = self.n + 1
        
        aux_graph = defaultdict(list)
        aux_cap = {}
        
        def add_aux_edge(frm, to, cap):
            aux_cap[(frm, to)] = cap
            aux_graph[frm].append(to)
            aux_graph[to].append(frm)  # 双向
        
        # Step 1: 添加所有原始边（容量 = upper - lower）
        for (u, v), ub in self.upper.items():
            lb = self.lower[(u, v)]
            residual = ub - lb
            add_aux_edge(u, v, residual)
        
        # Step 2: 计算每个节点的净流量需求
        demand = [0] * self.n
        
        for (u, v), lb in self.lower.items():
            demand[u] -= lb  # 流出下界
            demand[v] += lb  # 流入下界
        
        # Step 3: 添加从 super_source 和到 super_sink 的边
        for v in range(self.n):
            if v == self.source or v == self.sink:
                continue
            if demand[v] > 0:
                add_aux_edge(super_source, v, demand[v])
            elif demand[v] < 0:
                add_aux_edge(v, super_sink, -demand[v])
        
        # 处理源点和汇点
        # 汇点需要接收来自 super_source 的额外流量
        if demand[self.sink] > 0:
            add_aux_edge(super_source, self.sink, demand[self.sink])
        elif demand[self.sink] < 0:
            add_aux_edge(self.sink, super_sink, -demand[self.sink])
        
        # 源点需要向 super_sink 发送额外流量
        if demand[self.source] > 0:
            add_aux_edge(super_source, self.source, demand[self.source])
        elif demand[self.source] < 0:
            add_aux_edge(self.source, super_sink, -demand[self.source])
        
        # Step 4: 添加从原始汇到原始源的无穷容量边
        add_aux_edge(self.sink, self.source, float('inf'))
        
        # Step 5: 求 super_source 到 super_sink 的最大流
        total_demand = sum(d for d in demand if d > 0)
        max_flow_val = self._edmonds_karp(aux_graph, aux_cap, super_source, super_sink)
        
        if max_flow_val >= total_demand:
            # 可行流存在
            # 从辅助网络恢复原网络的流
            result_flow = {}
            for (u, v), lb in self.lower.items():
                forward_flow = lb + aux_cap.get((u, v), 0) - self._get_residual(aux_graph, aux_cap, u, v)
                result_flow[(u, v)] = max(lb, forward_flow)
            return True, result_flow
        else:
            return False, {}
    
    def _get_residual(self, graph, cap, u, v):
        """获取残留容量"""
        # 简化：从cap字典计算
        if (u, v) in cap:
            return cap[(u, v)]
        return 0
    
    def _edmonds_karp(self, graph, capacity, source, sink):
        """Edmonds-Karp 最大流"""
        flow = 0
        n_prime = self.n + 2
        
        while True:
            parent = {}
            queue = deque([source])
            parent[source] = None
            
            while queue and sink not in parent:
                u = queue.popleft()
                for v in graph[u]:
                    if v not in parent and capacity.get((u, v), 0) > 0:
                        parent[v] = u
                        queue.append(v)
            
            if sink not in parent:
                break
            
            # 找瓶颈
            path_flow = float('inf')
            v = sink
            while v != source:
                u = parent[v]
                path_flow = min(path_flow, capacity.get((u, v), 0))
                v = u
            
            # 增广
            v = sink
            while v != source:
                u = parent[v]
                capacity[(u, v)] -= path_flow
                capacity[(v, u)] = capacity.get((v, u), 0) + path_flow
                v = u
            
            flow += path_flow
        
        return flow


def build_lower_bound_example():
    """构建一个上下界测试问题"""
    # 4个节点，源=0，汇=3
    # 边: (u, v, lower, upper)
    n = 4
    source, sink = 0, 3
    
    lbf = LowerBoundFlow(n, source, sink)
    
    # 添加上下界边
    lbf.add_edge(0, 1, 1, 4)
    lbf.add_edge(0, 2, 0, 3)
    lbf.add_edge(1, 2, 1, 2)
    lbf.add_edge(1, 3, 2, 5)
    lbf.add_edge(2, 3, 1, 3)
    
    return lbf


if __name__ == "__main__":
    print("=" * 55)
    print("上下界网络流（Lower and Upper Bound Flow）")
    print("=" * 55)
    
    lbf = build_lower_bound_example()
    
    print("\n网络：源=0, 汇=3, 4节点")
    print("边及其上下界（lower, upper）：")
    print("  0->1: (1, 4)")
    print("  0->2: (0, 3)")
    print("  1->2: (1, 2)")
    print("  1->3: (2, 5)")
    print("  2->3: (1, 3)")
    
    print("\n检查是否存在可行流...")
    feasible, flow = lbf.check_feasible_flow()
    
    if feasible:
        print("\n✓ 存在可行流！")
        print("\n各边的流量：")
        for (u, v), f in sorted(flow.items()):
            lb = lbf.lower[(u, v)]
            ub = lbf.upper[(u, v)]
            print(f"  {u} -> {v}: 流量 {f} （下界{lb}, 上界{ub}）")
    else:
        print("\n✗ 不存在可行流")
