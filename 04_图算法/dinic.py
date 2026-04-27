# -*- coding: utf-8 -*-
"""
算法实现：04_图算法 / dinic

本文件实现 dinic 相关的算法功能。
"""

from __future__ import annotations

# INF: 代表无穷大（足够大的数）
INF = float("inf")


class Dinic:
    """
    Dinic 最大流算法实现类。
    
    Attributes:
        lvl: 层次图中每个顶点的层级
        ptr: 每个顶点的当前边指针（用于 DFS 避免重复）
        q: BFS 队列
        adj: 邻接表，每条边存储 [目标顶点, 反向边索引, 容量, 当前流量]
    """

    def __init__(self, n):
        """
        初始化 Dinic 算法结构。
        
        Args:
            n: 图中顶点的数量
        """
        self.lvl = [0] * n          # 顶点的层次（距离源点的最短路径）
        self.ptr = [0] * n          # 当前迭代中访问到的边位置
        self.q = [0] * n            # BFS 队列
        self.adj = [[] for _ in range(n)]  # 邻接表

    def add_edge(self, a, b, c, rcap=0):
        """
        添加一条有向边（带容量）。
        
        Args:
            a: 起点
            b: 终点
            c: 容量（正向边）
            rcap: 反向边的容量（默认0）
        """
        # 正向边：[终点, 反向边在adj[b]中的索引, 容量, 当前流量]
        self.adj[a].append([b, len(self.adj[b]), c, 0])
        # 反向边（用于增广路径）
        self.adj[b].append([a, len(self.adj[a]) - 1, rcap, 0])

    def depth_first_search(self, vertex, sink, flow):
        """
        在层次图中寻找增广路径（DFS）。
        
        Args:
            vertex: 当前顶点
            sink: 汇点
            flow: 当前路径的可用流量
        
        Returns:
            能到达汇点的流量（0表示没有增广路径）
        """
        # 到达汇点或没有可用流量时返回
        if vertex == sink or not flow:
            return flow

        for i in range(self.ptr[vertex], len(self.adj[vertex])):
            e = self.adj[vertex][i]
            # 只沿层次递增的边前进
            if self.lvl[e[0]] == self.lvl[vertex] + 1:
                # 递归寻找增广路径，限制流量
                p = self.depth_first_search(e[0], sink, min(flow, e[2] - e[3]))
                if p:
                    # 更新正向边流量
                    self.adj[vertex][i][3] += p
                    # 更新反向边流量
                    self.adj[e[0]][e[1]][3] -= p
                    return p
            # 移动指针，避免重复检查
            self.ptr[vertex] = self.ptr[vertex] + 1
        return 0

    def max_flow(self, source, sink):
        """
        计算从 source 到 sink 的最大流。
        
        Args:
            source: 源点
            sink: 汇点
        
        Returns:
            最大流量值
        """
        flow = 0
        self.q[0] = source
        # 最多迭代 31 次（适用于 32 位整数）
        for l in range(31):
            # 构建层次图
            while True:
                self.lvl = [0] * len(self.q)
                self.ptr = [0] * len(self.q)
                qi, qe, self.lvl[source] = 0, 1, 1
                # BFS 遍历
                while qi < qe and not self.lvl[sink]:
                    v = self.q[qi]
                    qi += 1
                    for e in self.adj[v]:
                        # 只经过还有剩余容量的边
                        if not self.lvl[e[0]] and (e[2] - e[3]) >> (30 - l):
                            self.q[qe] = e[0]
                            qe += 1
                            self.lvl[e[0]] = self.lvl[v] + 1

            # 寻找增广路径
            while True:
                p = self.depth_first_search(source, sink, INF)
                if not p:
                    break
                flow += p

            # 如果汇点不可达，算法结束
            if not self.lvl[sink]:
                break

        return flow


# ==========================================================
# 测试代码
# ==========================================================
if __name__ == "__main__":
    # 示例：二分图匹配
    # 顶点 1~4 靠近源点（左侧），顶点 5~8 靠近汇点（右侧）
    # 构建一个 10 顶点的图（0:源点，9:汇点）
    graph = Dinic(10)
    source = 0
    sink = 9

    # 源点到左侧顶点（容量1）
    for vertex in range(1, 5):
        graph.add_edge(source, vertex, 1)

    # 右侧顶点到汇点（容量1）
    for vertex in range(5, 9):
        graph.add_edge(vertex, sink, 1)

    # 左侧到右侧的边（匹配关系）
    for vertex in range(1, 5):
        graph.add_edge(vertex, vertex + 4, 1)

    # 计算最大匹配数
    result = graph.max_flow(source, sink)
    print(f"最大流（匹配数）: {result}")
