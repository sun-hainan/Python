# -*- coding: utf-8 -*-
"""
算法实现：参数算法 / euler_path

本文件实现 euler_path 相关的算法功能。
"""

def has_eulerian_path(graph):
    """
    判断无向图是否有欧拉路径或欧拉回路。

    定理：
    - 如果所有顶点度数为偶数，则存在欧拉回路
    - 如果恰好有 0 或 2 个奇度数顶点，则存在欧拉路径

    参数:
        graph: 邻接表表示的无向图

    返回:
        0: 无欧拉路径
        1: 有欧拉路径（但无回路）
        2: 有欧拉回路
    """
    if not graph:
        return 2

    odd_degree_vertices = []
    for v in graph:
        deg = len(graph[v])
        if deg % 2 == 1:
            odd_degree_vertices.append(v)

    if len(odd_degree_vertices) == 0:
        return 2   # 欧拉回路
    elif len(odd_degree_vertices) == 2:
        return 1   # 欧拉路径
    else:
        return 0   # 无


def find_eulerian_path(graph, start=None):
    """
    使用 Hierholzer 算法找到欧拉路径或回路。

    参数:
        graph: 邻接表（会被修改，需提前复制）
        start: 起始顶点（如果有欧拉路径则必须是奇度顶点之一）

    返回:
        欧拉路径经过的顶点序列
    """
    # 复制图以避免修改原图
    g = {v: list(ngh) for v, ngh in graph.items()}

    # 确认图连通（从 start 可达所有非孤立点）
    if not g:
        return []

    if start is None:
        start = next(v for v in g if g[v])  # 取第一个有边的顶点

    # Hierholzer 算法
    stack = [start]
    path = []

    while stack:
        v = stack[-1]
        if g.get(v):
            # 取出第一条边
            u = g[v].pop()
            # 删除反向边
            if u in g[v]:
                g[v].remove(u)
            if v in g.get(u, []):
                g[u].remove(v)

            stack.append(u)
        else:
            path.append(stack.pop())

    path.reverse()
    return path


def is_connected(graph):
    """检查图是否连通（忽略孤立顶点）。"""
    if not graph:
        return True

    vertices_with_edges = [v for v in graph if graph[v]]
    if not vertices_with_edges:
        return True

    start = vertices_with_edges[0]
    visited = set()
    stack = [start]

    while stack:
        v = stack.pop()
        if v in visited:
            continue
        visited.add(v)
        for u in graph.get(v, []):
            if u not in visited:
                stack.append(u)

    return len(visited) == len(vertices_with_edges)


if __name__ == "__main__":
    # 测试1：欧拉回路
    euler_circuit = {
        0: [1, 3],
        1: [0, 2, 3],
        2: [1, 3],
        3: [0, 1, 2]
    }

    # 测试2：欧拉路径
    euler_path = {
        0: [1],
        1: [0, 2],
        2: [1, 3],
        3: [2]
    }

    # 测试3：无欧拉路径
    no_euler = {
        0: [1, 2],
        1: [0],
        2: [0, 3],
        3: [2]
    }

    for name, g in [("欧拉回路", euler_circuit),
                     ("欧拉路径", euler_path),
                     ("无欧拉路径", no_euler)]:
        print(f"\n=== {name} ===")
        print(f"图: {g}")
        print(f"连通性: {is_connected(g)}")
        kind = has_eulerian_path(g)
        print(f"类型: {'回路' if kind == 2 else '路径' if kind == 1 else '无'}")

        if kind:
            path = find_eulerian_path(g)
            print(f"路径: {path}")
            # 验证路径长度
            print(f"路径长度(边数): {len(path) - 1}")
