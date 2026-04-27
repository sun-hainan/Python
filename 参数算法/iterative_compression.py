# -*- coding: utf-8 -*-
"""
算法实现：参数算法 / iterative_compression

本文件实现 iterative_compression 相关的算法功能。
"""

def iterative_compression_fvs(graph, k):
    """
    迭代压缩求解反馈顶点集：删除最少的顶点使图无环。

    参数:
        graph: 有向图的邻接表表示
        k: 参数，最多允许删除的顶点数

    返回:
        删除的顶点集合，或 None（如果无解）
    """
    n = len(graph)

    # 从空图开始，逐步加入顶点
    compressed = {}   # 当前已压缩的无环子图

    for v in range(n):
        # 将顶点 v 加入当前图
        compressed[v] = list(graph.get(v, []))

        # 用迭代压缩在 k 限制内找覆盖
        solution = compress_fvs(compressed, k)
        if solution is None:
            return None

        # 如果解的大小超过 k，无解
        if len(solution) > k:
            return None

    return solution


def compress_fvs(graph, k):
    """
    给定一个已经几乎无环的图 G'，压缩找到更小的 FVS。
    graph 已经有 n-1 个顶点无环，只需处理第 n 个顶点。

    这是一个简化版本：直接穷举所有 size <= k 的子集来验证。

    参数:
        graph: 当前图
        k: 允许的删除顶点数

    返回:
        大小 <= k 的 FVS
    """
    vertices = list(graph.keys())
    n = len(vertices)

    # 对每个顶点子集 S，检查 G - S 是否无环
    for subset in _subsets(vertices, k):
        if _is_acyclic(_remove_vertices(graph, subset)):
            return list(subset)

    # 没找到，返回空
    return []


def _is_acyclic(graph):
    """检查有向图是否无环（使用 Kahn 算法）。"""
    # 计算入度
    in_degree = {}
    for v in graph:
        in_degree.setdefault(v, 0)
        for u in graph.get(v, []):
            in_degree.setdefault(u, 0)
            in_degree[u] += 1

    # 将所有入度为 0 的顶点入队
    from collections import deque
    queue = deque([v for v in graph if in_degree.get(v, 0) == 0])
    visited = 0

    while queue:
        v = queue.popleft()
        visited += 1
        for u in graph.get(v, []):
            in_degree[u] -= 1
            if in_degree[u] == 0:
                queue.append(u)

    return visited == len(graph)


def _remove_vertices(graph, vertices_to_remove):
    """从图中删除指定顶点，返回新图。"""
    removed_set = set(vertices_to_remove)
    new_graph = {}
    for v, ngh in graph.items():
        if v in removed_set:
            continue
        new_graph[v] = [u for u in ngh if u not in removed_set]
    return new_graph


def _subsets(vertices, k):
    """生成所有 k 元子集。"""
    if k == 0:
        yield []
        return
    if not vertices or k < 0:
        return
    for rest in _subsets(vertices[1:], k):
        yield rest
    for rest in _subsets(vertices[1:], k - 1):
        yield [vertices[0]] + rest


if __name__ == "__main__":
    # 构造一个有向图：有环但可以通过删除少量顶点变无环
    test_graph = {
        0: [1],
        1: [2],
        2: [0, 3],   # 0->1->2->0 形成一个环
        3: [4],
        4: [5],
        5: [3]       # 3->4->5->3 形成另一个环
    }

    print("=== 迭代压缩 FVS 测试 ===")
    print(f"测试图: {test_graph}")

    for k in range(1, 4):
        import copy
        g = copy.deepcopy(test_graph)
        result = iterative_compression_fvs(g, k)
        if result is not None:
            print(f"\nk={k}: 找到 FVS = {result} (大小={len(result)})")
            # 验证
            remaining = _remove_vertices(test_graph, result)
            is_acyclic = _is_acyclic(remaining)
            print(f"  验证：删除后图无环 = {is_acyclic}")
        else:
            print(f"\nk={k}: 无解")
