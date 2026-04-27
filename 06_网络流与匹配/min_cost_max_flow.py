# -*- coding: utf-8 -*-

"""

算法实现：06_网络流与匹配 / min_cost_max_flow



本文件实现 min_cost_max_flow 相关的算法功能。

"""



import heapq

from collections import defaultdict





def build_flow_network():

    """构建一个带费用的网络示例（6节点）"""

    # 邻接表存储：(to, capacity, cost, reverse_index)

    graph = defaultdict(list)

    

    def add_edge(frm, to, cap, cost):

        """添加一条有向边及其反向边"""

        graph[frm].append([to, cap, cost, len(graph[to])])

        graph[to].append([frm, 0, -cost, len(graph[frm]) - 1])

    

    # 源点0 -> 汇点5

    # 0: 源

    add_edge(0, 1, 4, 2)   # 0->1，容量4，费用2

    add_edge(0, 2, 6, 1)   # 0->2，容量6，费用1

    add_edge(1, 3, 3, 3)   # 1->3，容量3，费用3

    add_edge(1, 2, 2, 2)   # 1->2，容量2，费用2

    add_edge(2, 3, 4, 1)   # 2->3，容量4，费用1

    add_edge(2, 4, 2, 4)   # 2->4，容量2，费用4

    add_edge(3, 5, 5, 2)   # 3->5，容量5，费用2

    add_edge(4, 5, 3, 1)   # 4->5，容量3，费用1

    

    return graph





def spfa(graph, n, source, sink):

    """

    SPFA（Shortest Path Faster Algorithm）求最短路

    返回：(distance, predecessor, found)

    """

    INF = float('inf')

    dist = [INF] * n       # 到各点的最短距离

    prev = [-1] * n        # 前驱边信息：(node, edge_idx)

    in_queue = [False] * n

    

    dist[source] = 0

    queue = [source]

    in_queue[source] = True

    

    while queue:

        u = queue.pop(0)

        in_queue[u] = False

        

        for i, edge in enumerate(graph[u]):

            to, cap, cost, rev = edge

            # 如果还有容量且可以改善距离

            if cap > 0 and dist[u] + cost < dist[to]:

                dist[to] = dist[u] + cost

                prev[to] = (u, i)

                if not in_queue[to]:

                    queue.append(to)

                    in_queue[to] = True

    

    return dist, prev, dist[sink] != INF





def min_cost_max_flow(graph, n, source, sink, max_flow=None):

    """

    最小费用最大流主算法（SSP）

    

    参数：

        graph: 邻接表

        n: 节点总数

        source: 源点

        sink: 汇点

        max_flow: 最大流量限制（None表示不限制）

    

    返回：(total_flow, total_cost, flow_matrix)

    """

    total_flow = 0

    total_cost = 0

    flow = defaultdict(int)  # 记录每条边的实际流量

    

    while True:

        # 找最短增广路

        dist, prev, found = spfa(graph, n, source, sink)

        if not found:

            break  # 无法找到增广路

        

        # 计算瓶颈容量

        bottleneck = float('inf')

        v = sink

        while v != source:

            u, ei = prev[v]

            edge = graph[u][ei]

            bottleneck = min(bottleneck, edge[1])  # edge[1] 是剩余容量

            v = u

        

        # 如果限制了最大流量

        if max_flow is not None:

            bottleneck = min(bottleneck, max_flow - total_flow)

            if bottleneck <= 0:

                break

        

        # 增广流量

        v = sink

        while v != source:

            u, ei = prev[v]

            edge = graph[u][ei]

            # 减少正向边的容量

            edge[1] -= bottleneck

            # 增加反向边的容量

            graph[v][edge[3]][1] += bottleneck

            # 记录流量

            key = (u, v)

            flow[key] = flow[key] + bottleneck

            total_cost += bottleneck * edge[2]  # edge[2] 是费用

            v = u

        

        total_flow += bottleneck

        print(f"  增广流量 {bottleneck}，累计流量 {total_flow}，累计费用 {total_cost}")

    

    return total_flow, total_cost, dict(flow)





def print_result(flow, cost):

    """打印最小费用最大流的详细结果"""

    print(f"\n最小费用最大流结果：")

    print(f"  最大流量 = {flow}")

    print(f"  最小费用 = {cost}")

    print(f"  单位流量费用 = {cost / flow:.2f}")





if __name__ == "__main__":

    print("=" * 50)

    print("最小费用最大流 - SSP 算法")

    print("=" * 50)

    

    # 构庺网络

    graph = build_flow_network()

    n = 6  # 6个节点：0为源，5为汇

    

    print("\n网络拓扑（源=0, 汇=5）：")

    print("  0 -> 1 (cap=4, cost=2)")

    print("  0 -> 2 (cap=6, cost=1)")

    print("  1 -> 3 (cap=3, cost=3)")

    print("  1 -> 2 (cap=2, cost=2)")

    print("  2 -> 3 (cap=4, cost=1)")

    print("  2 -> 4 (cap=2, cost=4)")

    print("  3 -> 5 (cap=5, cost=2)")

    print("  4 -> 5 (cap=3, cost=1)")

    print()

    print("增广过程：")

    

    # 计算最小费用最大流

    flow, cost, flow_detail = min_cost_max_flow(graph, n, source=0, sink=5)

    

    print_result(flow, cost)

    

    print("\n各边的流量分布：")

    for (u, v), f in sorted(flow_detail.items()):

        if f > 0:

            print(f"  边 {u} -> {v}：流量 {f}")

