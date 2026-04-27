# -*- coding: utf-8 -*-

"""

算法实现：04_图算法 / articulation_points



本文件实现 articulation_points 相关的算法功能。

"""



def compute_ap(graph):

    """

    计算无向图中的所有割点。

    

    Args:

        graph: 邻接表表示的图，字典格式 {顶点: [邻接顶点列表]}

    

    Returns:

        打印所有割点的索引

    

    示例图：

        0 --- 1      5 --- 6

        |  X  |      |  X  |

        2 --- 3 --- 4 --- 7 --- 8

    

    其中 2 和 5 是割点

    """

    n = len(graph)

    out_edge_count = 0

    # low[u]: u 能追溯到的最早祖先的发现时间

    low = [0] * n

    # visited[u]: u 是否已被访问

    visited = [False] * n

    # is_art[u]: u 是否为割点

    is_art = [False] * n



    def dfs(root, at, parent, out_edge_count):

        """

        DFS 递归遍历，维护时间戳和 low 值。

        

        Args:

            root: DFS 树的根顶点

            at: 当前访问的顶点

            parent: 当前顶点的父顶点

            out_edge_count: 根顶点的子树数量

        

        Returns:

            更新后的 out_edge_count

        """

        # 根顶点需要特殊处理：有两个以上子树才可能是割点

        if parent == root:

            out_edge_count += 1

        visited[at] = True

        low[at] = at



        for to in graph[at]:

            if to == parent:

                pass

            elif not visited[to]:

                # 递归访问子节点

                out_edge_count = dfs(root, to, at, out_edge_count)

                # 更新 low 值：取min(low[at], low[to])

                low[at] = min(low[at], low[to])



                # 通过桥发现的割点：low[to] >= dfn[at]

                if at < low[to]:

                    is_art[at] = True

                # 通过环发现的割点：low[to] == dfn[at]

                if at == low[to]:

                    is_art[at] = True

            else:

                # 后向边：更新 low 值

                low[at] = min(low[at], to)

        return out_edge_count



    # 遍历所有连通分量

    for i in range(n):

        if not visited[i]:

            out_edge_count = 0

            out_edge_count = dfs(i, i, -1, out_edge_count)

            # 根顶点特殊判断：出边数 > 1 才为割点

            is_art[i] = out_edge_count > 1



    # 输出所有割点

    for x in range(len(is_art)):

        if is_art[x] is True:

            print(x)





# ==========================================================

# 测试代码

# ==========================================================

if __name__ == "__main__":

    # 示例图（9个顶点）

    # 0 - 1 - 2

    #     |   |

    #     3   4

    #     |   |

    #     5 - 6 - 7 - 8

    # 割点为 2 和 5

    graph = {

        0: [1, 2],

        1: [0, 2],

        2: [0, 1, 3, 5],

        3: [2, 4],

        4: [3],

        5: [2, 6, 8],

        6: [5, 7],

        7: [6, 8],

        8: [5, 7],

    }

    print("割点（应为 2 和 5）:")

    compute_ap(graph)

