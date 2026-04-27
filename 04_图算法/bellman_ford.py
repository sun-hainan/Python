# -*- coding: utf-8 -*-
"""
算法实现：04_图算法 / bellman_ford

本文件实现 bellman_ford 相关的算法功能。
"""

from __future__ import annotations


def print_distance(distance: list[float], src):
    """打印从源点到各顶点的最短距离"""
    print(f"顶点\t从顶点 {src} 出发的最短距离")
    for i, d in enumerate(distance):
        print(f"{i}\t\t{d}")


def check_negative_cycle(
    graph: list[dict[str, int]], distance: list[float], edge_count: int
):
    """
    检测负环：进行第 V 次松弛操作

    如果还能松弛，说明存在负环。
    """
    for j in range(edge_count):
        u, v, w = (graph[j][k] for k in ["src", "dst", "weight"])
        if distance[u] != float("inf") and distance[u] + w < distance[v]:
            return True
    return False


def bellman_ford(
    graph: list[dict[str, int]], vertex_count: int, edge_count: int, src: int
) -> list[float]:
    """
    Bellman-Ford 算法

    参数:
        graph: 边列表，每条边格式 {"src": int, "dst": int, "weight": int}
        vertex_count: 顶点数
        edge_count: 边数
        src: 源点索引

    返回:
        从源点到各顶点的最短距离列表

    示例:
        >>> edges = [(2, 1, -10), (3, 2, 3), (0, 3, 5), (0, 1, 4)]
        >>> g = [{"src": s, "dst": d, "weight": w} for s, d, w in edges]
        >>> bellman_ford(g, 4, 4, 0)
        [0.0, -2.0, 8.0, 5.0]
    """
    # 初始化距离数组
    distance = [float("inf")] * vertex_count
    distance[src] = 0.0

    # 进行 V-1 次松弛操作
    for _ in range(vertex_count - 1):
        for j in range(edge_count):
            u, v, w = (graph[j][k] for k in ["src", "dst", "weight"])

            # 如果能通过边 (u,v) 找到更短的路径
            if distance[u] != float("inf") and distance[u] + w < distance[v]:
                distance[v] = distance[u] + w

    # 检测负环
    negative_cycle_exists = check_negative_cycle(graph, distance, edge_count)
    if negative_cycle_exists:
        raise Exception("检测到负环，无法计算最短路径")

    return distance


if __name__ == "__main__":
    import doctest
    doctest.testmod()

    V = int(input("输入顶点数: ").strip())
    E = int(input("输入边数: ").strip())

    graph: list[dict[str, int]] = [{} for _ in range(E)]

    for i in range(E):
        print(f"边 {i + 1}")
        src, dest, weight = (
            int(x)
            for x in input("输入源点 目标点 权重: ").strip().split(" ")
        )
        graph[i] = {"src": src, "dst": dest, "weight": weight}

    source = int(input("\n输入最短路径的源点: ").strip())
    shortest_distance = bellman_ford(graph, V, E, source)
    print_distance(shortest_distance, source)
