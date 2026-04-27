# -*- coding: utf-8 -*-

"""

算法实现：Graphs / 06_Floyd_Warshall



本文件实现 06_Floyd_Warshall 相关的算法功能。

"""



def floyd_warshall(graph):

    """

    Floyd-Warshall全源最短路径

    """

    n = len(graph)

    dist = [row[:] for row in graph]

    for k in range(n):

        for i in range(n):

            for j in range(n):

                if dist[i][k] + dist[k][j] < dist[i][j]:

                    dist[i][j] = dist[i][k] + dist[k][j]

    return dist





if __name__ == "__main__":

    # 测试: floyd_warshall

    result = floyd_warshall()

    print(result)

