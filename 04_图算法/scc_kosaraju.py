# -*- coding: utf-8 -*-

"""

算法实现：04_图算法 / scc_kosaraju



本文件实现 scc_kosaraju 相关的算法功能。

"""



from __future__ import annotations





# 全局变量（简化实现）

graph: list[list[int]] = []

reversed_graph: list[list[int]] = []

n: int = 0

scc: list[list[int]] = []

stack: list[int] = []

visit: list[bool] = []





def dfs(u: int):

    """第一次 DFS：记录 finish 顺序"""

    global graph, stack, visit

    if visit[u]:

        return

    visit[u] = True

    for v in graph[u]:

        dfs(v)

    stack.append(u)  # 后序遍历，最后完成的先入栈





def dfs2(u: int):

    """第二次 DFS：在转置图上遍历，得到一个 SCC"""

    global reversed_graph, visit, scc, component

    if visit[u]:

        return

    visit[u] = True

    component.append(u)

    for v in reversed_graph[u]:

        dfs2(v)





def kosaraju() -> list[list[int]]:

    """

    Kosaraju 算法主函数



    返回:

        强连通分量列表



    示例:

        # 7个顶点，9条边的图

        # n=7, edges=[(0,1),(0,3),(1,2),(2,0),(3,4),(4,5),(4,6),(6,5),(5,4)]

        # 结果: [[5], [6], [4], [3, 2, 1, 0]]

    """

    global graph, reversed_graph, n, scc, visit, stack, component



    # 第一次 DFS：记录完成顺序

    for i in range(n):

        if not visit[i]:

            dfs(i)



    # 重置访问标记

    visit = [False] * n



    # 按完成时间的逆序处理（相当于 Tarjan 的栈弹出）

    for i in stack[::-1]:

        if visit[i]:

            continue

        component = []

        dfs2(i)

        scc.append(component)



    return scc





if __name__ == "__main__":

    # 输入：n=顶点数, m=边数

    # 之后 m 行，每行一个边的起点和终点

    n_input, m_input = map(int, input("输入顶点数和边数: ").strip().split())



    graph = [[] for _ in range(n_input)]        # 原图

    reversed_graph = [[] for _ in range(n_input)]  # 转置图



    for _ in range(m_input):

        u, v = map(int, input().strip().split())

        graph[u].append(v)

        reversed_graph[v].append(u)  # 转置：边方向反转



    # 初始化全局变量

    graph = graph

    reversed_graph = reversed_graph

    n = n_input

    scc = []

    component = []

    stack = []

    visit = [False] * n



    result = kosaraju()

    print(f"强连通分量: {result}")

