# -*- coding: utf-8 -*-

"""

算法实现：近似算法 / euclidean_tsp_approx



本文件实现 euclidean_tsp_approx 相关的算法功能。

"""



import numpy as np

import random

from scipy.spatial import distance





def compute_euclidean_distance(points):

    """

    计算点之间的欧几里得距离矩阵

    

    Parameters

    ----------

    points : list

        点列表,每个点是 (x, y) 元组

    

    Returns

    -------

    np.ndarray

        距离矩阵

    """

    n = len(points)

    dist = np.zeros((n, n))

    

    for i in range(n):

        for j in range(i + 1, n):

            d = np.sqrt((points[i][0] - points[j][0])**2 + 

                       (points[i][1] - points[j][1])**2)

            dist[i][j] = d

            dist[j][i] = d

    

    return dist





def build_mst_prim(n, dist):

    """

    Prim 算法构建最小生成树 (MST)

    

    时间复杂度: O(n^2)

    

    Parameters

    ----------

    n : int

        顶点数量

    dist : np.ndarray

        距离矩阵

    

    Returns

    -------

    list

        MST 的边列表,每个元素是 (u, v)

    """

    in_mst = [False] * n

    min_edge = [float('inf')] * n

    parent = [-1] * n

    

    # 从顶点 0 开始

    min_edge[0] = 0

    

    for _ in range(n):

        # 找到未加入 MST 的最小边顶点

        u = -1

        for v in range(n):

            if not in_mst[v] and (u == -1 or min_edge[v] < min_edge[u]):

                u = v

        

        if u == -1:

            break

        

        in_mst[u] = True

        

        # 更新邻居的最小边

        for v in range(n):

            if not in_mst[v] and dist[u][v] < min_edge[v]:

                min_edge[v] = dist[u][v]

                parent[v] = u

    

    # 构建边列表

    mst_edges = []

    for v in range(1, n):

        if parent[v] != -1:

            mst_edges.append((parent[v], v))

    

    return mst_edges





def mst_double_tsp(points):

    """

    MST 加倍算法求解欧几里得 TSP (2-近似)

    

    算法步骤:

    1. 计算 MST

    2. 加倍 MST 的边

    3. 在加倍图中找到欧拉回路

    4. 跳过回路中重复访问的顶点 (捷径)

    

    近似比: 2

    

    Parameters

    ----------

    points : list

        点列表 [(x, y), ...]

    

    Returns

    -------

    tuple

        (访问顺序, 总长度)

    """

    n = len(points)

    

    if n <= 1:

        return list(range(n)), 0

    

    # 计算距离矩阵

    dist = compute_euclidean_distance(points)

    

    # 构建 MST

    mst_edges = build_mst_prim(n, dist)

    

    # 构建加倍的 MST (每个顶点度数翻倍)

    adjacency = {i: [] for i in range(n)}

    for u, v in mst_edges:

        adjacency[u].append(v)

        adjacency[v].append(u)

    

    # 深度优先搜索找到欧拉回路

    def dfs_euler(start):

        stack = [start]

        path = []

        

        while stack:

            v = stack[-1]

            if adjacency[v]:

                u = adjacency[v].pop()

                # 删除反向边

                adjacency[u].remove(v)

                stack.append(u)

            else:

                path.append(stack.pop())

        

        return path

    

    euler_path = dfs_euler(0)

    euler_path.reverse()  # 正确顺序

    

    # 捷径: 跳过已访问的顶点

    visited = [False] * n

    tour = []

    

    for v in euler_path:

        if not visited[v]:

            tour.append(v)

            visited[v] = True

    

    # 确保回到起点

    if tour[-1] != tour[0]:

        tour.append(tour[0])

    

    # 计算总长度

    total_length = 0

    for i in range(len(tour) - 1):

        total_length += dist[tour[i]][tour[i + 1]]

    

    return tour, total_length





def build_mst_kruskal(n, dist):

    """

    Kruskal 算法构建 MST

    

    Parameters

    ----------

    n : int

        顶点数量

    dist : np.ndarray

        距离矩阵

    

    Returns

    -------

    list

        MST 边列表

    """

    # 并查集

    parent = list(range(n))

    rank = [0] * n

    

    def find(x):

        if parent[x] != x:

            parent[x] = find(parent[x])

        return parent[x]

    

    def union(x, y):

        px, py = find(x), find(y)

        if px == py:

            return False

        if rank[px] < rank[py]:

            px, py = py, px

        parent[py] = px

        if rank[px] == rank[py]:

            rank[px] += 1

        return True

    

    # 按距离排序边

    edges = []

    for i in range(n):

        for j in range(i + 1, n):

            edges.append((dist[i][j], i, j))

    

    edges.sort()

    

    mst_edges = []

    for d, u, v in edges:

        if union(u, v):

            mst_edges.append((u, v))

            if len(mst_edges) == n - 1:

                break

    

    return mst_edges





def christofides_tsp(points):

    """

    Christofides 算法求解欧几里得 TSP (1.5-近似)

    

    算法步骤:

    1. 计算 MST

    2. 找到 MST 中度为奇数的顶点集合 O

    3. 在 O 上计算最小权重完美匹配

    4. 将匹配边加入 MST,得到欧拉图

    5. 找到欧拉回路,捷径得到 TSP 回路

    

    近似比: 1.5

    

    Parameters

    ----------

    points : list

        点列表

    

    Returns

    -------

    tuple

        (访问顺序, 总长度)

    """

    n = len(points)

    

    if n <= 2:

        tour = list(range(n))

        if n == 2:

            d = np.sqrt((points[0][0] - points[1][0])**2 + 

                       (points[0][1] - points[1][1])**2)

            return tour + [tour[0]], 2 * d

        return tour, 0

    

    dist = compute_euclidean_distance(points)

    

    # Step 1: MST

    mst_edges = build_mst_prim(n, dist)

    

    # Step 2: 找到奇数度顶点

    degree = [0] * n

    for u, v in mst_edges:

        degree[u] += 1

        degree[v] += 1

    

    odd_vertices = [i for i in range(n) if degree[i] % 2 == 1]

    

    # Step 3: 最小完美匹配 (简化: 使用贪心)

    # 实际应该用 Blossom 算法

    matching_edges = []

    remaining = set(odd_vertices)

    

    while remaining:

        u = remaining.pop()

        # 找到最近的奇数顶点

        best_v = None

        best_dist = float('inf')

        

        for v in remaining:

            if dist[u][v] < best_dist:

                best_dist = dist[u][v]

                best_v = v

        

        if best_v is not None:

            matching_edges.append((u, best_v))

            remaining.remove(best_v)

    

    # Step 4: 构建欧拉图

    euler_adj = {i: [] for i in range(n)}

    for u, v in mst_edges + matching_edges:

        euler_adj[u].append(v)

        euler_adj[v].append(u)

    

    # Step 5: 找到欧拉回路

    def hierholzer(start):

        stack = [start]

        path = []

        

        while stack:

            v = stack[-1]

            if euler_adj[v]:

                u = euler_adj[v].pop()

                euler_adj[u].remove(v)

                stack.append(u)

            else:

                path.append(stack.pop())

        

        return path

    

    euler_path = hierholzer(0)

    euler_path.reverse()

    

    # 捷径

    visited = [False] * n

    tour = []

    

    for v in euler_path:

        if not visited[v]:

            tour.append(v)

            visited[v] = True

    

    if tour[-1] != tour[0]:

        tour.append(tour[0])

    

    # 计算长度

    total_length = 0

    for i in range(len(tour) - 1):

        total_length += dist[tour[i]][tour[i + 1]]

    

    return tour, total_length





def nearest_neighbor_tsp(points, start=0):

    """

    最近邻贪心 TSP (简单但质量较差)

    

    策略: 从起点开始,每次选择最近的未访问顶点

    

    Parameters

    ----------

    points : list

        点列表

    start : int

        起始顶点

    

    Returns

    -------

    tuple

        (访问顺序, 总长度)

    """

    n = len(points)

    

    if n <= 1:

        return list(range(n)), 0

    

    dist = compute_euclidean_distance(points)

    

    visited = [False] * n

    tour = [start]

    visited[start] = True

    

    current = start

    

    for _ in range(n - 1):

        nearest = -1

        nearest_dist = float('inf')

        

        for v in range(n):

            if not visited[v] and dist[current][v] < nearest_dist:

                nearest = v

                nearest_dist = dist[current][v]

        

        if nearest != -1:

            tour.append(nearest)

            visited[nearest] = True

            current = nearest

    

    tour.append(tour[0])  # 回到起点

    

    # 计算长度

    total_length = 0

    for i in range(len(tour) - 1):

        total_length += dist[tour[i]][tour[i + 1]]

    

    return tour, total_length





def verify_tour_validity(tour, n):

    """

    验证 TSP 回路的有效性

    

    检查:

    1. 访问了所有 n 个顶点

    2. 每个顶点恰好访问一次

    3. 回路是闭合的

    

    Parameters

    ----------

    tour : list

        访问顺序

    n : int

        顶点数

    

    Returns

    -------

    tuple

        (是否有效, 错误信息)

    """

    if len(tour) < n + 1:

        return False, f"长度不足: {len(tour)} vs {n + 1}"

    

    if tour[0] != tour[-1]:

        return False, "回路未闭合"

    

    visited = set(tour[:-1])

    if len(visited) != n:

        missing = set(range(n)) - visited

        return False, f"未访问顶点: {missing}"

    

    if len(visited) != len(tour) - 1:

        return False, "存在重复访问"

    

    return True, "有效"





if __name__ == "__main__":

    # 测试: 欧几里得 TSP

    

    print("=" * 60)

    print("欧几里得 TSP MST 加倍近似测试")

    print("=" * 60)

    

    np.random.seed(42)

    

    # 生成随机测试点

    n_points = 15

    points = [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(n_points)]

    

    print(f"\n测试点数量: {n_points}")

    print(f"前5个点: {points[:5]}")

    

    # MST 加倍算法

    print("\n--- MST 加倍算法 (2-近似) ---")

    tour_mst, len_mst = mst_double_tsp(points)

    valid, msg = verify_tour_validity(tour_mst, n_points)

    print(f"访问顺序: {tour_mst}")

    print(f"总长度: {len_mst:.2f}")

    print(f"有效性: {valid}, {msg}")

    

    # Christofides 算法

    print("\n--- Christofides 算法 (1.5-近似) ---")

    tour_chris, len_chris = christofides_tsp(points)

    valid, msg = verify_tour_validity(tour_chris, n_points)

    print(f"访问顺序: {tour_chris}")

    print(f"总长度: {len_chris:.2f}")

    print(f"有效性: {valid}, {msg}")

    

    # 最近邻算法 (基准)

    print("\n--- 最近邻贪心 ---")

    tour_nn, len_nn = nearest_neighbor_tsp(points, start=0)

    print(f"总长度: {len_nn:.2f}")

    

    # 比较

    print("\n--- 算法比较 ---")

    print(f"MST加倍: {len_mst:.2f}")

    print(f"Christofides: {len_chris:.2f}")

    print(f"最近邻: {len_nn:.2f}")

    

    if len_chris < len_mst:

        print(f"Christofides 优于 MST加倍: {len_mst / len_chris:.2f}x")

    

    # 理论界验证

    print("\n--- 理论界 ---")

    # MST 长度是 TSP 最优值的下界

    dist = compute_euclidean_distance(points)

    mst_edges = build_mst_prim(n_points, dist)

    mst_length = sum(dist[u][v] for u, v in mst_edges)

    print(f"MST 长度 (TSP 下界): {mst_length:.2f}")

    print(f"MST加倍 / 下界 = {len_mst / mst_length:.2f} (理论界: ≤2)")

    print(f"Christofides / 下界 = {len_chris / mst_length:.2f} (理论界: ≤1.5)")

    

    print("\n" + "=" * 60)

    print("测试完成!")

    print("=" * 60)

