# -*- coding: utf-8 -*-

"""

算法实现：06_网络流与匹配 / capacity_scaling



本文件实现 capacity_scaling 相关的算法功能。

"""



from collections import defaultdict, deque





def build_scaling_network():

    """构建测试网络"""

    graph = defaultdict(list)

    edges = {}

    

    def add_edge(frm, to, cap):

        idx = len(edges)

        edges[idx] = {'to': to, 'cap': cap, 'flow': 0}

        graph[frm].append(('forward', idx))

        

        rev_idx = len(edges)

        edges[rev_idx] = {'to': frm, 'cap': 0, 'flow': 0}

        graph[to].append(('backward', rev_idx))

        

        return idx, rev_idx

    

    # 源点0，汇点5

    add_edge(0, 1, 10)

    add_edge(0, 2, 10)

    add_edge(1, 2, 2)

    add_edge(1, 3, 4)

    add_edge(1, 4, 8)

    add_edge(2, 4, 9)

    add_edge(3, 4, 6)

    add_edge(3, 5, 10)

    add_edge(4, 5, 10)

    

    return graph, edges





def get_max_capacity(edges):

    """获取图中最大容量"""

    max_cap = 0

    for eid, edge in edges.items():

        if edge['cap'] > max_cap:

            max_cap = edge['cap']

    return max_cap





def bfs_scaling(graph, edges, source, sink, delta):

    """

    在缩放图上 BFS 找增广路

    只考虑残留容量 >= delta 的边

    """

    parent = {}

    queue = deque([source])

    parent[source] = None

    

    while queue:

        u = queue.popleft()

        

        if u == sink:

            return True, parent

        

        for etype, eid in graph[u]:

            edge = edges[eid]

            v = edge['to']

            

            if v not in parent:

                residual = edge['cap'] - edge['flow'] if etype == 'forward' else edge['flow']

                if residual >= delta:

                    parent[v] = (u, etype, eid)

                    queue.append(v)

    

    return False, parent





def capacity_scaling_max_flow(graph, edges, source, sink):

    """

    容量缩放最大流算法

    

    返回：(max_flow_value, num_iterations)

    """

    # 获取最大容量并设为初始 Δ

    max_cap = get_max_capacity(edges)

    delta = 1

    while max_cap >= delta:

        delta *= 2

    delta //= 2  # 回到最大的 2 的幂次

    

    if delta == 0:

        delta = 1

    

    total_flow = 0

    iteration = 0

    

    print(f"初始缩放因子 Δ = {delta}")

    

    while delta >= 1:

        iteration += 1

        print(f"\n--- 阶段 Δ = {delta} ---")

        

        # 使用当前 Δ 找增广路

        while True:

            found, parent = bfs_scaling(graph, edges, source, sink, delta)

            

            if not found:

                break

            

            # 计算瓶颈容量

            bottleneck = float('inf')

            v = sink

            path_edges = []

            

            while v != source:

                u, etype, eid = parent[v]

                edge = edges[eid]

                residual = edge['cap'] - edge['flow'] if etype == 'forward' else edge['flow']

                bottleneck = min(bottleneck, residual)

                path_edges.append((v, etype, eid))

                v = u

            

            # 增广

            for v, etype, eid in path_edges:

                if etype == 'forward':

                    edges[eid]['flow'] += bottleneck

                else:

                    edges[eid]['flow'] -= bottleneck

            

            total_flow += bottleneck

            print(f"  迭代 {iteration}: 增广 {bottleneck}，累计 {total_flow}")

        

        delta //= 2  # 缩小 Δ

    

    return total_flow, iteration





def print_network_flow(edges):

    """打印各边的流量和容量"""

    print("\n各边流量详情：")

    shown = set()

    for eid, edge in edges.items():

        if eid % 2 == 0:  # 只显示正向边

            # 找到对应的反向边

            rev_eid = eid + 1

            if rev_eid in edges:

                flow_sent = edges[rev_eid]['flow']  # 反向边的flow表示流出的量

                print(f"  边 {eid//2}: 流量 {flow_sent}")

                shown.add(eid)





if __name__ == "__main__":

    print("=" * 55)

    print("容量缩放法（Capacity Scaling）求最大流")

    print("=" * 55)

    

    graph, edges = build_scaling_network()

    

    print("\n网络：源=0, 汇=5")

    print("边及容量：")

    print("  0->1(10), 0->2(10), 1->2(2), 1->3(4), 1->4(8)")

    print("  2->4(9), 3->4(6), 3->5(10), 4->5(10)")

    

    source, sink = 0, 5

    

    print("\n开始计算...")

    max_flow, iters = capacity_scaling_max_flow(graph, edges, source, sink)

    

    print(f"\n{'='*55}")

    print(f"最大流 = {max_flow}")

    print(f"总迭代次数 = {iters}")

