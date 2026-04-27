# -*- coding: utf-8 -*-

"""

算法实现：Graphs / 03_Dijkstra



本文件实现 03_Dijkstra 相关的算法功能。

"""



import heapq



def dijkstra(graph, start, end):

    """

    Dijkstra最短路径

    """

    heap = [(0, start)]

    visited = set()

    while heap:

        dist, vertex = heapq.heappop(heap)

        if vertex in visited:

            continue

        visited.add(vertex)

        if vertex == end:

            return dist

        for neighbor, weight in graph.get(vertex, []):

            if neighbor not in visited:

                heapq.heappush(heap, (dist + weight, neighbor))

    return -1





if __name__ == "__main__":

    # 测试: dijkstra

    result = dijkstra()

    print(result)

