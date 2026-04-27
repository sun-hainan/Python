# -*- coding: utf-8 -*-

"""

算法实现：04_图算法 / strongly_connected_components



本文件实现 strongly_connected_components 相关的算法功能。

"""



# 测试图1（3个 SCC：{0,1,2}, {3}, {4}）

test_graph_1 = {0: [2, 3], 1: [0], 2: [1], 3: [4], 4: []}



# 测试图2（2个 SCC：{0,1,2}, {3,4,5}）

test_graph_2 = {0: [1, 2, 3], 1: [2], 2: [0], 3: [4], 4: [5], 5: [3]}





def topology_sort(

    graph: dict[int, list[int]], vert: int, visited: list[bool]

) -> list[int]:

    """

    拓扑排序（DFS 实现），用于获取顶点的处理顺序。

    

    Args:

        graph: 邻接表表示的图

        vert: 当前访问的顶点

        visited: 访问标记数组

    

    Returns:

        按后序遍历顺序的顶点列表

    

    示例:

    >>> topology_sort(test_graph_1, 0, 5 * [False])

    [1, 2, 4, 3, 0]

    """

    visited[vert] = True

    order = []



    for neighbour in graph[vert]:

        if not visited[neighbour]:

            order += topology_sort(graph, neighbour, visited)



    order.append(vert)



    return order





def find_components(

    reversed_graph: dict[int, list[int]], vert: int, visited: list[bool]

) -> list[int]:

    """

    在逆图上 DFS，寻找同一强连通分量中的所有顶点。

    

    Args:

        reversed_graph: 逆图（所有边方向反转）

        vert: 当前访问的顶点

        visited: 访问标记数组

    

    Returns:

        当前 SCC 中的所有顶点列表

    

    示例:

    >>> find_components({0: [1], 1: [2], 2: [0]}, 0, 5 * [False])

    [0, 1, 2]

    """

    visited[vert] = True

    component = [vert]



    for neighbour in reversed_graph[vert]:

        if not visited[neighbour]:

            component += find_components(reversed_graph, neighbour, visited)



    return component





def strongly_connected_components(graph: dict[int, list[int]]) -> list[list[int]]:

    """

    计算有向图中所有强连通分量。

    

    Args:

        graph: 邻接表表示的有向图

    

    Returns:

        所有强连通分量的列表，每个分量是一个顶点列表

    

    算法步骤：

    1. 在原图上拓扑排序，获取顶点的处理顺序

    2. 在逆图上按逆序遍历，未访问的顶点属于同一个 SCC

    

    示例:

    >>> strongly_connected_components(test_graph_1)

    [[0, 1, 2], [3], [4]]

    >>> strongly_connected_components(test_graph_2)

    [[0, 2, 1], [3, 5, 4]]

    """

    # 第一步：获取拓扑排序顺序

    visited = len(graph) * [False]

    order = []

    for i, was_visited in enumerate(visited):

        if not was_visited:

            order += topology_sort(graph, i, visited)



    # 第二步：构建逆图

    reversed_graph: dict[int, list[int]] = {vert: [] for vert in range(len(graph))}

    for vert, neighbours in graph.items():

        for neighbour in neighbours:

            reversed_graph[neighbour].append(vert)



    # 第三步：在逆图上按逆序寻找 SCC

    components_list = []

    visited = len(graph) * [False]



    for i in range(len(graph)):

        vert = order[len(graph) - i - 1]

        if not visited[vert]:

            component = find_components(reversed_graph, vert, visited)

            components_list.append(component)



    return components_list





# ==========================================================

# 测试代码

# ==========================================================

if __name__ == "__main__":

    # 测试图1

    print("=== 测试图1 ===")

    print("图结构:", test_graph_1)

    scc1 = strongly_connected_components(test_graph_1)

    print("强连通分量:", scc1)

    print("预期: [[0, 1, 2], [3], [4]]")

    

    # 测试图2

    print("\n=== 测试图2 ===")

    print("图结构:", test_graph_2)

    scc2 = strongly_connected_components(test_graph_2)

    print("强连通分量:", scc2)

    print("预期: [[0, 2, 1], [3, 5, 4]]")

