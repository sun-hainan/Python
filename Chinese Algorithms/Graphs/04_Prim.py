# -*- coding: utf-8 -*-

"""

算法实现：Graphs / 04_Prim



本文件实现 04_Prim 相关的算法功能。

"""



def prim(graph):

    """

    Prim最小生成树

    """

    n = len(graph)

    visited = [False] * n

    min_dist = [float('inf')] * n

    min_dist[0] = 0

    result = 0

    for _ in range(n):

        u = -1

        for v in range(n):

            if not visited[v]:

                if u == -1 or min_dist[v] < min_dist[u]:

                    u = v

        if min_dist[u] == float('inf'):

            break

        visited[u] = True

        result += min_dist[u]

        for v in range(n):

            if graph[u][v] > 0 and not visited[v]:

                min_dist[v] = min(min_dist[v], graph[u][v])

    return result





if __name__ == "__main__":

    # 测试: prim

    result = prim()

    print(result)

