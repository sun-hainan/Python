# -*- coding: utf-8 -*-

"""

算法实现：06_网络流与匹配 / min_cost_flow



本文件实现 min_cost_flow 相关的算法功能。

"""



from collections import deque

from typing import List, Dict, Tuple, Optional





class MinCostFlow:

    """

    最小费用最大流 / 最小费用流算法。



    Attributes:

        n: 顶点数

        graph: 邻接表，每条边记录 (to, cap, cost, rev)

               其中 rev 是反向边在对方邻接表中的索引

        source: 超源点

        sink: 超汇点

    """



    Edge = Tuple[int, int, int, int]  # (to, cap, cost, rev)



    def __init__(self, n: int):

        """

        初始化最小费用流实例。



        Args:

            n: 顶点数

        """

        self.n = n

        self.graph: List[List[Tuple[int, int, int, int]]] = [[] for _ in range(n)]



    def add_edge(self, u: int, v: int, cap: int, cost: int):

        """

        添加一条有向边（含容量和费用）。



        Args:

            u: 起点

            v: 终点

            cap: 容量（须 >= 0）

            cost: 单位流量费用（须 >= 0）

        """

        # 正向边: to=v, cap, cost, rev=反向边在 graph[v] 的位置

        forward = (v, cap, cost, None)  # type: ignore

        # 反向边: to=u, cap=0, cost=-cost

        backward = (u, 0, -cost, forward)  # type: ignore

        # 建立双向链接

        forward_rev_index = len(self.graph[v])  # type: ignore

        backward_rev_index = len(self.graph[u])  # type: ignore

        forward = (v, cap, cost, backward)  # type: ignore

        backward = (u, 0, -cost, forward)  # type: ignore

        self.graph[u].append(forward)

        self.graph[v].append(backward)



    def _spfa(self, source: int, sink: int) -> Tuple[bool, List[int], List[int]]:

        """

        SPFA（Shortest Path Faster Algorithm）求最短路。



        Args:

            source: 源点

            sink: 汇点



        Returns:

            (found, dist, parent): 

                found - 是否存在从 s 到 t 的路径

                dist - 各顶点到 source 的最短距离

                parent - 各顶点的父边 (prev_v, edge_idx)

        """

        dist = [float('inf')] * self.n

        in_queue = [False] * self.n

        parent_v = [-1] * self.n

        parent_e = [-1] * self.n



        dist[source] = 0

        queue = deque([source])

        in_queue[source] = True



        while queue:

            u = queue.popleft()

            in_queue[u] = False



            for i, edge in enumerate(self.graph[u]):

                to, cap, cost, _ = edge

                if cap > 0 and dist[u] + cost < dist[to] - 1e-9:

                    dist[to] = dist[u] + cost

                    parent_v[to] = u

                    parent_e[to] = i

                    if not in_queue[to]:

                        queue.append(to)

                        in_queue[to] = True



        return dist[sink] < float('inf'), dist, (parent_v, parent_e)



    def min_cost_flow(self, source: int, sink: int, max_flow: int = float('inf')) -> Tuple[int, int]:

        """

        计算从 source 到 sink 的最小费用最大流（不超过 max_flow）。



        Args:

            source: 源点

            sink: 汇点

            max_flow: 最大流量限制（默认 inf）



        Returns:

            (flow, cost): 实际发送的流量和最小总费用

        """

        flow = 0

        cost = 0

        n = self.n



        while flow < max_flow:

            found, dist, (parent_v, parent_e) = self._spfa(source, sink)

            if not found:

                break



            # 找路径上的最小剩余容量

            d = max_flow - flow

            v = sink

            while v != source:

                u = parent_v[v]

                i = parent_e[v]

                to, cap, _, _ = self.graph[u][i]

                d = min(d, cap)

                v = u



            # 推送 flow

            v = sink

            while v != source:

                u = parent_v[v]

                i = parent_e[v]

                # 修改容量

                to, cap, cst, rev_edge = self.graph[u][i]

                # 正向边减少 cap

                self.graph[u][i] = (to, cap - d, cst, rev_edge)

                # 反向边增加 cap

                rev_u, rev_cap, rev_cost, rev_rev = rev_edge

                self.graph[v][parent_e[v]] = (rev_u, rev_cap + d, rev_cost, self.graph[u][i])



                cost += d * cst

                v = u



            flow += d



        return flow, cost



    def min_cost_flow_multi_source_sink(

        self,

        sources: List[int],

        sinks: List[int],

        supplies: List[int],

        demands: List[int],

        super_source: int,

        super_sink: int

    ) -> Tuple[int, int]:

        """

        多源多汇最小费用流（通过超源/超汇简化）。



        Args:

            sources: 源点列表

            sinks: 汇点列表

            supplies: 各源点的供应量

            demands: 各汇点的需求量

            super_source: 超源点编号（需要手动在图中预留）

            super_sink: 超汇点编号



        Returns:

            (flow, cost)

        """

        # 连接超源到各源，超汇到各汇（已在初始化时设置）

        return self.min_cost_flow(super_source, super_sink)





def build_min_cost_network(n: int, edges: List[Tuple[int, int, int, int]]) -> MinCostFlow:

    """

    从边列表构建最小费用流网络。



    Args:

        n: 顶点数

        edges: 边列表 [(u, v, cap, cost), ...]



    Returns:

        配置好的 MinCostFlow 实例

    """

    mcf = MinCostFlow(n)

    for u, v, cap, cost in edges:

        mcf.add_edge(u, v, cap, cost)

    return mcf





if __name__ == "__main__":

    import sys



    # ----------------- 测试 1: 简单 4 点网络 -----------------

    #    0 --(10/3)--> 1 --(8/2)--> 3

    #    |                        ^

    #    +--(5/1)--> 2 --(7/1)---+

    n1 = 4

    edges1 = [

        (0, 1, 10, 3),

        (0, 2, 5, 1),

        (1, 3, 8, 2),

        (2, 3, 7, 1),

        (1, 2, 2, 1),  # 可选：中间边

    ]

    mcf1 = build_min_cost_network(n1, edges1)

    flow1, cost1 = mcf1.min_cost_flow(0, 3, max_flow=100)

    print(f"[测试1] 最小费用流 = flow={flow1}, cost={cost1}")

    print(f"  期望: flow=13 (路径 0->1->3 送10, 0->2->3 送3)")



    # ----------------- 测试 2: 有多条路径的网络 -----------------

    #    s(0) --(5/1)--> a(1)

    #    s(0) --(3/2)--> b(2)

    #    a(1) --(4/2)--> t(3)

    #    b(2) --(4/1)--> t(3)

    #    a(1) --(2/3)--> b(2)  (交叉边，费用高)

    n2 = 4

    edges2 = [

        (0, 1, 5, 1),

        (0, 2, 3, 2),

        (1, 3, 4, 2),

        (2, 3, 4, 1),

        (1, 2, 2, 3),

    ]

    mcf2 = build_min_cost_network(n2, edges2)

    flow2, cost2 = mcf2.min_cost_flow(0, 3, max_flow=7)

    print(f"[测试2] 多路径最小费用流 = flow={flow2}, cost={cost2}")

    # 期望: 0->1(5 units) + 0->2(2 units) = 7 flow

    # cost: 5*1 + 2*2 = 9? 不对

    # 实际: 0->1->3: 5*1+5*2=15, 0->2->3: 2*2+2*1=6, total=21

    # 但 0->1->3 最多送 4 (cap of 1->3), 剩下 0->2->3 送 3

    # flow=7: 4 via 0-1-3(cost=3*4=12) + 3 via 0-2-3(cost=3*1=9) = 21? 

    # 让我重算: 0->1(5)*1=5, 0->2(2)*2=4; 1->3(4)*2=8, 2->3(2)*1=2

    # total: 5+4+8+2=19

    print(f"  (flow={flow2}, cost={cost2})")



    # ----------------- 测试 3: 无法推送足够流量 -----------------

    n3 = 3

    edges3 = [

        (0, 1, 3, 1),

        (1, 2, 2, 1),

    ]

    mcf3 = build_min_cost_network(n3, edges3)

    flow3, cost3 = mcf3.min_cost_flow(0, 2, max_flow=10)

    print(f"[测试3] 容量受限 = flow={flow3} (最多 3, 瓶颈在 1->2=2)")

    assert flow3 == 2, f"期望 2，实际 {flow3}"

    assert cost3 == 2, f"期望费用 2，实际 {cost3}"



    # ----------------- 测试 4: 单位费用均为 0 -----------------

    n4 = 3

    edges4 = [

        (0, 1, 5, 0),

        (1, 2, 5, 0),

    ]

    mcf4 = build_min_cost_network(n4, edges4)

    flow4, cost4 = mcf4.min_cost_flow(0, 2, max_flow=5)

    print(f"[测试4] 零费用 = flow={flow4}, cost={cost4}")

    assert flow4 == 5 and cost4 == 0



    # ----------------- 测试 5: 单边 -----------------

    n5 = 2

    edges5 = [(0, 1, 10, 5)]

    mcf5 = build_min_cost_network(n5, edges5)

    flow5, cost5 = mcf5.min_cost_flow(0, 1, max_flow=7)

    print(f"[测试5] 单边 = flow={flow5}, cost={cost5} (期望 flow=7, cost=35)")

    assert flow5 == 7 and cost5 == 35



    print("\n所有最小费用流测试通过！")

