# -*- coding: utf-8 -*-

"""

算法实现：06_网络流与匹配 / hopcroft_karp



本文件实现 hopcroft_karp 相关的算法功能。

"""



from collections import deque





def build_bipartite_graph():

    """

    构建一个二分图示例

    左端点：0, 1, 2, 3（n=4）

    右端点：0', 1', 2', 3', 4'（m=5）

    

    边：

    0 -> 0', 1', 3'

    1 -> 1', 2'

    2 -> 0', 2', 4'

    3 -> 2', 3'

    """

    # adj_left[i] = list of right nodes connected to left node i

    adj_left = [

        [0, 1, 3],  # 左节点0 连到右节点0,1,3

        [1, 2],     # 左节点1 连到右节点1,2

        [0, 2, 4],  # 左节点2 连到右节点0,2,4

        [2, 3],     # 左节点3 连到右节点2,3

    ]

    return adj_left





def hopcroft_karp(adj_left, n_left, n_right):

    """

    Hopcroft-Karp 算法求二分图最大匹配

    

    参数：

        adj_left: 左节点邻接表

        n_left: 左节点数量

        n_right: 右节点数量

    

    返回：

        max_matching_size, matching

        其中 matching[left] = right 或 -1

    """

    INF = float('inf')

    

    # 匹配结果：matching_left[l] = r, matching_right[r] = l

    matching_left = [-1] * n_left

    matching_right = [-1] * n_right

    

    # dist[l] = BFS层数距离

    dist = [0] * n_left

    

    def bfs():

        """BFS 构建分层图，返回是否还有增广路"""

        queue = deque()

        

        # 初始化所有左节点

        for l in range(n_left):

            if matching_left[l] == -1:

                # 自由节点，层数为0

                dist[l] = 0

                queue.append(l)

            else:

                dist[l] = INF

        

        dist_nil = INF  # 虚拟汇点的距离

        

        while queue:

            l = queue.popleft()

            

            if dist[l] < dist_nil:

                for r in adj_left[l]:

                    # 相邻的右节点

                    ml = matching_right[r]

                    if ml == -1:

                        # 找到自由左节点，增广路终点

                        dist_nil = dist[l] + 1

                    elif dist[ml] == INF:

                        dist[ml] = dist[l] + 1

                        queue.append(ml)

        

        return dist_nil != INF

    

    def dfs(l):

        """DFS 寻找从左节点 l 出发的增广路"""

        for r in adj_left[l]:

            ml = matching_right[r]

            if ml == -1 or (dist[ml] == dist[l] + 1 and dfs(ml)):

                # 找到增广路，更新匹配

                matching_left[l] = r

                matching_right[r] = l

                return True

        dist[l] = INF  # 标记为死路

        return False

    

    matching_size = 0

    iteration = 0

    

    while bfs():

        iteration += 1

        print(f"  BFS层 {iteration}: 剩余自由节点", 

              sum(1 for l in range(n_left) if matching_left[l] == -1))

        

        # 尝试从每个自由左节点找增广路

        for l in range(n_left):

            if matching_left[l] == -1:

                if dfs(l):

                    matching_size += 1

    

    return matching_size, matching_left





def print_matching(matching, adj_left):

    """打印匹配详情"""

    print("\n匹配结果：")

    n_left = len(matching)

    matched = 0

    for l in range(n_left):

        r = matching[l]

        if r != -1:

            matched += 1

            print(f"  左节点 {l} <-> 右节点 {r}")

            print(f"    (通过边: {adj_left[l]})")

    print(f"\n最大匹配大小 = {matched}")





if __name__ == "__main__":

    print("=" * 55)

    print("Hopcroft-Karp 二分图最大匹配算法")

    print("=" * 55)

    

    adj_left = build_bipartite_graph()

    n_left = 4

    n_right = 5

    

    print(f"\n二分图：左{n_left}节点，右{n_right}节点")

    print("邻接表：")

    for i, neighbors in enumerate(adj_left):

        print(f"  左{i} -> 右{neighbors}")

    

    print("\n算法执行过程：")

    max_matching, matching = hopcroft_karp(adj_left, n_left, n_right)

    

    print_matching(matching, adj_left)

    

    print(f"\n验证: 匹配{'是' if max_matching == len([m for m in matching if m != -1]) else '否'}最大匹配")

