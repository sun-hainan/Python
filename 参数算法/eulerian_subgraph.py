# -*- coding: utf-8 -*-

"""

算法实现：参数算法 / eulerian_subgraph



本文件实现 eulerian_subgraph 相关的算法功能。

"""



def make_eulerian_min_edges(graph, k):

    """

    计算将无向图变成欧拉图所需删除的最少边数。



    思路：图 G 是欧拉的当且仅当所有顶点度数为偶数。

    通过添加虚拟边可以将奇度顶点两两配对。



    参数:

        graph: 邻接表

        k: 允许删除的最大边数



    返回:

        (min_edges_to_remove, matching): 最少删除边数及配对方案

    """

    # 计算所有奇度数顶点

    odd_vertices = [v for v in graph if len(graph[v]) % 2 == 1]



    if len(odd_vertices) <= 2:

        # 已经是欧拉路径或回路

        return 0, []



    # 需要添加的虚拟边数（等于 odd_vertices // 2）

    num_pairs = len(odd_vertices) // 2



    # 用贪婪匹配（简化，实际应用应使用完美匹配算法）

    matching = []

    available = odd_vertices[:]

    while len(available) >= 2:

        # 选择一对顶点添加虚拟边

        u = available.pop()

        v = available.pop()

        matching.append((u, v))



    # 计算每对虚拟边对应图中多少条最短路径上的边

    # 简化：用两顶点间直接边代替

    edges_to_remove = []

    for u, v in matching:

        # 模拟删除 u-v 边（实际图中可能不存在）

        edges_to_remove.append((u, v))



    return num_pairs, matching





def find_minimum_edges_to_eulerian(graph):

    """

    找到使图变为欧拉图所需删除的最小边集合。



    实际是找最小匹配问题，用 Floyd-Warshall + 动态规划求解。

    """

    vertices = list(graph.keys())

    n = len(vertices)

    idx = {v: i for i, v in enumerate(vertices)}



    # 构建距离矩阵（用于计算顶点间最短路径）

    dist = [[float('inf')] * n for _ in range(n)]

    for i in range(n):

        dist[i][i] = 0

    for v in graph:

        vi = idx[v]

        for u in graph[v]:

            if u in idx:

                dist[vi][idx[u]] = 1



    # Floyd-Warshall

    for w in range(n):

        for u in range(n):

            for v in range(n):

                if dist[u][v] > dist[u][w] + dist[w][v]:

                    dist[u][v] = dist[u][w] + dist[w][v]



    # 找所有奇度顶点

    odd = [i for i, v in enumerate(vertices) if len(graph.get(v, [])) % 2 == 1]



    if not odd:

        return 0, []



    # DP 求最小完美匹配（状态压缩）

    # dp[mask] = 最小配对代价

    m = len(odd)

    dp = [float('inf')] * (1 << m)

    dp[0] = 0



    for mask in range(1 << m):

        # 找到第一个未配对的顶点

        i = 0

        while i < m and (mask & (1 << i)):

            i += 1

        if i >= m:

            continue



        # 将 i 与后面某个未配对的顶点 j 配对

        for j in range(i + 1, m):

            if not (mask & (1 << j)):

                new_mask = mask | (1 << i) | (1 << j)

                # 配对代价：i 和 j 之间的距离

                cost = dist[odd[i]][odd[j]]

                dp[new_mask] = min(dp[new_mask], dp[mask] + cost)



    best_mask = (1 << m) - 1

    return dp[best_mask], odd





if __name__ == "__main__":

    # 测试图

    test_graph = {

        0: [1, 2],

        1: [0, 2],

        2: [0, 1, 3],

        3: [2, 4],

        4: [3]

    }



    print("=== 欧拉化最小边删除 ===")

    print(f"测试图: {test_graph}")



    min_cost, odd = find_minimum_edges_to_eulerian(test_graph)

    print(f"\n奇度数顶点: {odd}")

    print(f"最小删除代价: {min_cost}")



    # 另一个测试：完全图

    complete_graph = {

        0: [1, 2, 3],

        1: [0, 2, 3],

        2: [0, 1, 3],

        3: [0, 1, 2]

    }

    print(f"\n完全图 K4:")

    min_cost, odd = find_minimum_edges_to_eulerian(complete_graph)

    print(f"  奇度数顶点: {odd}")

    print(f"  最小删除代价: {min_cost}")

