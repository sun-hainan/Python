# -*- coding: utf-8 -*-
"""
算法实现：06_网络流与匹配 / dinic_flow

本文件实现 dinic_flow 相关的算法功能。
"""

from collections import defaultdict, deque


class DinicMaxFlow:
    """Dinic 最大流算法"""
    
    def __init__(self, n):
        self.n = n
        self.graph = defaultdict(list)
    
    def add_edge(self, u, v, cap):
        """添加有向边"""
        forward = {
            'to': v,
            'cap': cap,
            'flow': 0,
            'rev': len(self.graph[v])
        }
        backward = {
            'to': u,
            'cap': 0,
            'flow': 0,
            'rev': len(self.graph[u])
        }
        
        self.graph[u].append(forward)
        self.graph[v].append(backward)
    
    def bfs_level(self, source, sink):
        """
        BFS 构建分层图
        
        返回：
            level[v] = 源到 v 的最短距离（跳数）
            如果 v 不可达，level[v] = -1
        """
        level = [-1] * self.n
        level[source] = 0
        
        queue = deque([source])
        
        while queue:
            u = queue.popleft()
            for edge in self.graph[u]:
                v = edge['to']
                residual = edge['cap'] - edge['flow']
                
                if residual > 0 and level[v] < 0:
                    level[v] = level[u] + 1
                    queue.append(v)
        
        return level
    
    def dfs_blocking_flow(self, u, sink, level, it, flow):
        """
        DFS 找阻塞流
        
        参数：
            u: 当前节点
            sink: 汇点
            level: 分层信息
            it: 当前弧指针（用于当前弧优化）
            flow: 请求的流量
        
        返回：实际推送的流量
        """
        if u == sink:
            return flow
        
        for i in range(it[u], len(self.graph[u])):
            edge = self.graph[u][i]
            v = edge['to']
            residual = edge['cap'] - edge['flow']
            
            if residual > 0 and level[v] == level[u] + 1:
                pushed = self.dfs_blocking_flow(v, sink, level, it, min(flow, residual))
                
                if pushed > 0:
                    # 增广
                    edge['flow'] += pushed
                    self.graph[v][edge['rev']]['flow'] -= pushed
                    return pushed
            
            it[u] += 1
        
        return 0
    
    def max_flow(self, source, sink):
        """
        Dinic 主算法
        
        返回：最大流值
        """
        flow = 0
        n = self.n
        
        iteration = 0
        
        while True:
            # Step 1: BFS 构建分层图
            level = self.bfs_level(source, sink)
            
            if level[sink] < 0:
                break  # 汇不可达
            
            # Step 2: DFS 找阻塞流
            it = [0] * n  # 当前弧指针
            blocked = False
            
            while not blocked:
                iteration += 1
                pushed = self.dfs_blocking_flow(source, sink, level, it, float('inf'))
                
                if pushed == 0:
                    blocked = True
                else:
                    flow += pushed
                    if iteration % 5 == 0:
                        print(f"  阻塞流迭代 {iteration}: 累计流量 {flow}")
        
        return flow


def build_dinic_network():
    """构建测试网络"""
    n = 7
    dinic = DinicMaxFlow(n)
    
    # 创建一个更复杂的网络
    edges = [
        (0, 1, 10), (0, 2, 10),  # 源出边
        (1, 3, 5), (1, 4, 5),   # 第一层
        (2, 3, 5), (2, 4, 5),   # 第一层到第二层
        (3, 5, 8), (4, 5, 8),   # 出边
        (1, 2, 2),              # 交叉边
        (3, 4, 3),              # 额外边
        (3, 6, 5), (4, 6, 5),  # 侧边
        (6, 5, 10),            # 侧边汇合
    ]
    
    for u, v, cap in edges:
        dinic.add_edge(u, v, cap)
    
    return dinic


if __name__ == "__main__":
    print("=" * 55)
    print("Dinic 最大流算法")
    print("=" * 55)
    
    dinic = build_dinic_network()
    
    print("\n网络：源=0, 汇=5, 7节点")
    print("边及容量：")
    print("  0->1(10), 0->2(10), 1->3(5), 1->4(5)")
    print("  2->3(5), 2->4(5), 3->5(8), 4->5(8)")
    print("  1->2(2), 3->4(3), 3->6(5), 4->6(5), 6->5(10)")
    
    print("\n算法执行：")
    max_flow = dinic.max_flow(source=0, sink=5)
    
    print(f"\n{'='*55}")
    print(f"最大流 = {max_flow}")
