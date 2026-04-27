# -*- coding: utf-8 -*-

"""

算法实现：04_图算法 / depth_first_search



本文件实现 depth_first_search 相关的算法功能。

"""



from __future__ import annotations





def depth_first_search(graph: dict, start: str) -> set[str]:

    """

    深度优先搜索（非递归实现，使用栈）



    算法步骤：

        1. 将起始顶点加入栈并标记已访问

        2. 从栈弹出一个顶点（后进先出）

        3. 访问该顶点，将未访问的邻接顶点入栈

        4. 重复直到栈为空



    与 BFS 的区别：

        1. 用栈（pop）代替队列（pop(0)）

        2. 将邻接顶点直接加入栈，而不是按顺序探索



    参数:

        graph: 有向图，以字典表示（key=顶点，value=邻接顶点列表）

        start: 起始顶点



    返回:

        所有可达顶点的集合



    示例:

        >>> input_G = {

        ...     "A": ["B", "C", "D"], "B": ["A", "D", "E"],

        ...     "C": ["A", "F"], "D": ["B", "D"], "E": ["B", "F"],

        ...     "F": ["C", "E", "G"], "G": ["F"]

        ... }

        >>> sorted(depth_first_search(input_G, "A"))

        ['A', 'B', 'C', 'D', 'E', 'F', 'G']

    """

    explored, stack = set([start]), [start]



    while stack:

        v = stack.pop()  # 弹出栈顶元素（后进先出）

        explored.add(v)



        # 逆序添加邻接顶点，使结果顺序与递归版一致

        for adj in reversed(graph[v]):

            if adj not in explored:

                stack.append(adj)



    return explored





# 示例图

G = {

    "A": ["B", "C", "D"],

    "B": ["A", "D", "E"],

    "C": ["A", "F"],

    "D": ["B", "D"],

    "E": ["B", "F"],

    "F": ["C", "E", "G"],

    "G": ["F"],

}





if __name__ == "__main__":

    import doctest

    doctest.testmod()

    print(f"DFS 从 A 开始: {sorted(depth_first_search(G, 'A'))}")

