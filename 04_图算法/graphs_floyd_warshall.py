# -*- coding: utf-8 -*-
"""
算法实现：04_图算法 / graphs_floyd_warshall

本文件实现 graphs_floyd_warshall 相关的算法功能。
"""

from typing import List


def _print_dist(dist: List[List[float]], v: int):
    """打印距离矩阵"""
    print("\n最短路径矩阵（Floyd-Warshall 算法）:\n")
    for i in range(v):
        for j in range(v):
            if dist[i][j] != float("inf"):
                print(int(dist[i][j]), end="\t")
            else:
                print("INF", end="\t")
        print()


def floyd_warshall(graph: List[List[float]], v: int) -> tuple:
    """
    Floyd-Warshall 全源最短路径算法

    参数:
        graph: 邻接矩阵，graph[i][j] = 边 (i,j) 的权重，无边为 INF
        v: 顶点数

    返回:
        (最短距离矩阵, 顶点数)

    示例:
        # 3 个顶点，2 条边：1->2 (权重2), 2->1 (权重1)
        >>> graph = [[0, INF, INF], [INF, 0, 2], [1, INF, 0]]
        >>> floyd_warshall(graph, 3)
        # 输出每对顶点间的最短距离
    """
    # 初始化距离矩阵
    dist = [[float("inf") for _ in range(v)] for _ in range(v)]

    # 从邻接矩阵初始化
    for i in range(v):
        for j in range(v):
            dist[i][j] = graph[i][j]

    # 动态规划：逐步引入中间顶点 k
    for k in range(v):
        for i in range(v):
            for j in range(v):
                # 如果经过 k 的路径更短，则更新
                if (
                    dist[i][k] != float("inf")
                    and dist[k][j] != float("inf")
                    and dist[i][k] + dist[k][j] < dist[i][j]
                ):
                    dist[i][j] = dist[i][k] + dist[k][j]

    _print_dist(dist, v)
    return dist, v


if __name__ == "__main__":
    v = int(input("输入顶点数: "))
    e = int(input("输入边数: "))

    graph = [[float("inf") for _ in range(v)] for _ in range(v)]
    for i in range(v):
        graph[i][i] = 0.0

    for i in range(e):
        print(f"\n边 {i + 1}")
        src = int(input("起点: "))
        dst = int(input("终点: "))
        weight = float(input("权重: "))
        graph[src][dst] = weight

    floyd_warshall(graph, v)
