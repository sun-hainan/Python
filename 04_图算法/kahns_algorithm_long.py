# -*- coding: utf-8 -*-

"""

算法实现：04_图算法 / kahns_algorithm_long



本文件实现 kahns_algorithm_long 相关的算法功能。

"""



def longest_distance(graph):

    """

    计算 DAG 中从任意起点到任意终点的最长路径长度。

    

    Args:

        graph: 邻接表表示的 DAG，格式 {源点: [终点列表]}

    

    Example:

        graph = {

            0: [2, 3, 4],   # 0 -> 2, 0 -> 3, 0 -> 4

            1: [2, 7],       # 1 -> 2, 1 -> 7

            2: [5],

            3: [5, 7],

            4: [7],

            5: [6],

            6: [7],

            7: []           # 终点无出边

        }

    """

    # 初始化入度数组

    indegree = [0] * len(graph)

    # BFS 队列（存储入度为 0 的顶点）

    queue = []

    # long_dist[i]: 以顶点 i 结尾的最长路径长度

    long_dist = [1] * len(graph)



    # 步骤1: 计算所有顶点的入度

    for values in graph.values():

        for i in values:

            indegree[i] += 1



    # 步骤2: 将入度为 0 的顶点入队（这些是拓扑排序的起点）

    for i in range(len(indegree)):

        if indegree[i] == 0:

            queue.append(i)



    # 步骤3: 按拓扑顺序处理

    while queue:

        # 弹出队首顶点

        vertex = queue.pop(0)

        # 遍历该顶点的所有出边

        for x in graph[vertex]:

            # 更新相邻顶点的入度

            indegree[x] -= 1



            # 动态规划：long_dist[x] = max(long_dist[x], long_dist[vertex] + 1)

            long_dist[x] = max(long_dist[x], long_dist[vertex] + 1)



            # 如果入度变为 0，加入队列

            if indegree[x] == 0:

                queue.append(x)



    # 步骤4: 输出最长路径

    print(max(long_dist))





# ==========================================================

# 测试代码

# ==========================================================

if __name__ == "__main__":

    # 示例 DAG（9 个顶点）

    # 结构如下：

    #     0

    #    /|\

    #   2 3 4

    #   | | |

    #   5 5 7

    #   | |

    #   6 7

    #    \|

    #     7

    graph = {

        0: [2, 3, 4],

        1: [2, 7],

        2: [5],

        3: [5, 7],

        4: [7],

        5: [6],

        6: [7],

        7: []

    }

    print("最长路径长度（应为 4）:")

    longest_distance(graph)

