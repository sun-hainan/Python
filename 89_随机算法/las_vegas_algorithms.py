# -*- coding: utf-8 -*-

"""

算法实现：随机算法 / las_vegas_algorithms



本文件实现拉斯维加斯（Las Vegas）算法家族。

拉斯维加斯算法的特点：

    - 随机化过程 + 确定性正确结果

    - 永不返回错误答案，只可能"找不到"并重试

    - 典型代表：随机化快速排序（主元随机）、Min-Cut



主要实现：

    - las_vegas_selection: 拉斯维加斯选择（找中位数，失败重试）

    - randomized_min_cut: 随机化最小割（Karger 算法）

"""

import random
import copy


def las_vegas_selection(arr: list, target_rank: int, max_attempts: int = 100) -> int:
    """
    拉斯维加斯风格的选择算法

    不断随机打乱数组，直到找到正确的第 target_rank 小的元素。
    永不返回错误答案——要么成功要么重试。

    参数：
        arr: 待搜索数组
        target_rank: 目标排名（从 1 开始）
        max_attempts: 最大尝试次数

    返回：
        第 target_rank 小的元素，如果所有尝试都失败则抛出异常
    """
    n = len(arr)
    for _ in range(max_attempts):
        # 随机打乱数组
        working_copy = arr.copy()
        random.shuffle(working_copy)

        # 检查排序后第 target_rank 小的位置是否正确
        sorted_copy = sorted(working_copy)
        candidate = sorted_copy[target_rank - 1]

        # 验证候选答案（双重保险）
        rank_count = sum(1 for x in arr if x < candidate)
        if rank_count == target_rank - 1:
            return candidate

    raise ValueError(f"经过 {max_attempts} 次尝试未能找到第 {target_rank} 小的元素")


def randomized_min_cut(graph: dict) -> list:
    """
    Karger 随机化最小割算法

    给定一个无向图，返回一个最小割集（边数最少的割）。

    算法流程：
        1. 随机选择一条边 (u, v)
        2. 合并 u 和 v 为单个顶点（收缩）
        3. 重复直到只剩 2 个顶点
        4. 这两个顶点之间的边数就是一个割的大小

    重复多次取最小值，失败概率随次数指数下降。

    参数：
        graph: 邻接表表示的图，格式 {顶点: [相邻顶点列表]}

    返回：
        一个最小割的边列表，每条边为 (u, v) 元组
    """
    # 如果图只有 2 个顶点，直接返回这两点之间的所有边
    vertices = list(graph.keys())
    if len(vertices) == 2:
        u, v = vertices
        return [(u, v) for _ in range(len(graph[u]))]

    # 随机选择一条边
    u = random.choice(vertices)
    if not graph[u]:
        return []

    v = random.choice(graph[u])

    # 收缩操作：合并 u 和 v 为 w
    w = (u, v)
    new_graph = copy.deepcopy(graph)

    # 将所有指向 v 的边改为指向 w
    for node in new_graph:
        new_graph[node] = [w if x == v else x for x in new_graph[node]]
        # 从 node 的邻接表中移除 self-loop（u-v 自环）
        new_graph[node] = [x for x in new_graph[node] if x != w or node != w]

    # 将 u 和 v 的邻接表合并（去重）
    neighbors_u = [x for x in new_graph[u] if x != w]
    neighbors_v = [x for x in new_graph[v] if x != w]
    merged = list(set(neighbors_u + neighbors_v))

    # 删除 u 和 v 节点
    del new_graph[u]
    del new_graph[v]

    # 添加新节点 w
    new_graph[w] = merged

    # 递归收缩直到只剩 2 个顶点
    return randomized_min_cut(new_graph)


def randomized_min_cut_once(graph: dict) -> tuple:
    """
    执行一次 Karger 收缩算法

    随机选择边并不断收缩，直到只剩 2 个顶点。
    返回割的边数和割的顶点对。

    参数：
        graph: 邻接表图

    返回：
        (割的大小, 两个顶点)
    """
    g = copy.deepcopy(graph)
    vertices = list(g.keys())

    while len(vertices) > 2:
        # 随机选择一个顶点 u
        u = random.choice(vertices)
        if not g[u]:
            break

        # 从 u 的邻接表中随机选择 v
        v = random.choice(g[u])

        # 收缩 u 和 v 为新顶点 w
        w = (u, v)

        # 更新所有邻接表中的 v -> w
        for node in g:
            g[node] = [w if x == v else x for x in g[node]]

        # 移除 self-loops
        for node in g:
            g[node] = [x for x in g[node] if x != w or node == w]

        # 合并 u 和 v 的邻接表
        neighbors_u = [x for x in g[u] if x != w]
        neighbors_v = [x for x in g[v] if x != w]
        merged = list(set(neighbors_u + neighbors_v))

        # 删除 u 和 v
        del g[u]
        del g[v]

        # 添加新顶点 w
        g[w] = merged
        vertices = list(g.keys())

    # 剩下的两个顶点之间的边数即为割的大小
    if len(vertices) == 2:
        a, b = vertices
        cut_size = len([x for x in g[a] if x == b])
        return cut_size, (a, b)

    return 0, (None, None)


def repeated_min_cut(graph: dict, repetitions: int = None) -> tuple:
    """
    重复 Karger 算法取最优解

    最小割大小至少为图的最小度数。
    为使成功率 > 99%，需要至少 n² 次尝试（n 为顶点数）。

    参数：
        graph: 邻接表图
        repetitions: 重复次数（默认 n²）

    返回：
        (最小割大小, 对应的两个顶点)
    """
    n = len(graph)
    if repetitions is None:
        repetitions = n * n

    best_cut = float('inf')
    best_pair = None

    for _ in range(repetitions):
        cut_size, pair = randomized_min_cut_once(graph)
        if cut_size < best_cut:
            best_cut = cut_size
            best_pair = pair

    return best_cut, best_pair


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 拉斯维加斯算法测试 ===\n")

    random.seed(42)

    # 测试 1: 拉斯维加斯选择
    print("--- 拉斯维加斯选择 ---")
    arr = [random.randint(1, 1000) for _ in range(50)]
    expected = sorted(arr)
    for rank in [1, 13, 25, 50]:
        result = las_vegas_selection(arr, rank)
        expected_val = expected[rank - 1]
        status = "✅" if result == expected_val else "❌"
        print(f"  找第 {rank} 小: {result} (期望 {expected_val}) {status}")

    # 测试 2: Karger 最小割
    print("\n--- Karger 随机化最小割 ---")

    # 构建一个简单的图：4 个顶点，完全图 K4 去掉一条边
    # 最小割应该是 2
    graph = {
        0: [1, 2, 3],
        1: [0, 2, 3],
        2: [0, 1, 3],
        3: [0, 1, 2],
    }

    # 去掉 (2, 3) 边，实际上完全图的最小割是 3
    graph = {
        0: [1, 2, 3],
        1: [0, 2, 3],
        2: [0, 1],
        3: [0, 1],
    }

    print("  测试图: K4 去掉一条边")
    for trial in range(5):
        cut_size, pair = randomized_min_cut_once(graph)
        print(f"  尝试 {trial + 1}: 割大小 = {cut_size}, 顶点对 = {pair}")

    # 重复多次取最优
    best_cut, best_pair = repeated_min_cut(graph, repetitions=100)
    print(f"\n  100 次重复最优: 割大小 = {best_cut}")

    # 测试 3: 更大规模的图
    print("\n--- 较大规模图测试 ---")

    def create_random_graph(n, edge_prob=0.5):
        """创建一个随机图（邻接表）"""
        g = {i: [] for i in range(n)}
        for i in range(n):
            for j in range(i + 1, n):
                if random.random() < edge_prob:
                    g[i].append(j)
                    g[j].append(i)
        return g

    for n in [10, 20]:
        g = create_random_graph(n, edge_prob=0.4)
        best_cut, _ = repeated_min_cut(g, repetitions=n * n)
        print(f"  n={n}: 最小割 ≈ {best_cut}")

    print("\n说明：")
    print("  - 拉斯维加斯算法：随机化 + 确定性正确（永不返回错误）")
    print("  - 拉斯维加斯选择：打乱直到正确（期望很快）")
    print("  - Karger Min-Cut: 收缩随机边，重复取最优")
    print("  - 重复 n² 次时，成功概率 > 99%")
