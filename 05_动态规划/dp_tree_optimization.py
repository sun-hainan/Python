# -*- coding: utf-8 -*-

"""

算法实现：05_动态规划 / dp_tree_optimization



本文件实现 dp_tree_optimization 相关的算法功能。

"""



from typing import List, Tuple, Optional

from collections import defaultdict





class TreeDP:

    """

    树形动态规划模板类

    

    提供两种基础模式：

    1. 向下DP（自底向上）：计算子树信息

    2. 换根DP：计算以每个节点为根时的答案

    """

    

    def __init__(self, n: int):

        """

        Args:

            n: 节点数量

        """

        self.n = n

        self.children: List[List[int]] = [[] for _ in range(n)]

        self.parent: List[int] = [-1] * n

        self.depth: List[int] = [0] * n

    

    def add_edge(self, u: int, v: int):

        """添加无向边"""

        self.children[u].append(v)

        self.children[v].append(u)

    

    def build_tree(self, root: int = 0):

        """

        从根节点开始构建树结构

        

        Args:

            root: 根节点ID

        """

        self.root = root

        self.parent[root] = -1

        self.depth[root] = 0

        self._dfs_build(root, -1)

    

    def _dfs_build(self, node: int, parent: int):

        """DFS构建树，记录父子关系和深度"""

        self.parent[node] = parent

        for child in self.children[node]:

            if child != parent:

                self.depth[child] = self.depth[node] + 1

                self._dfs_build(child, node)

    

    def dp_subtree(self, node: int, 

                   compute: callable) -> any:

        """

        计算以 node 为根的子树信息（自底向上）

        

        Args:

            node: 当前节点

            compute: 计算函数，参数为 (node, child_results)

        

        Returns:

            该子树的信息

        """

        child_results = []

        for child in self.children[node]:

            if child != self.parent[node]:

                child_results.append(self.dp_subtree(child, compute))

        return compute(node, child_results)

    

    def reroot_dp(self, 

                  init_state: callable,

                  merge: callable,

                  propagate: callable) -> List:

        """

        换根DP模板

        

        Args:

            init_state(node): 初始化节点状态

            merge(node, state, children_states): 合并子节点状态

            propagate(node, parent_state, child_states): 从父节点状态推导子节点状态

        

        Returns:

            每个节点的最终答案列表

        """

        # 第一步：自底向上，计算初始状态

        down_state: List[Optional[any]] = [None] * self.n

        

        def dfs_down(node: int, parent: int):

            child_states = []

            for child in self.children[node]:

                if child != parent:

                    dfs_down(child, node)

                    child_states.append(down_state[child])

            down_state[node] = merge(node, init_state(node), child_states)

        

        dfs_down(self.root, -1)

        

        # 第二步：自顶向下，换根传递

        result: List[Optional[any]] = [None] * self.n

        

        def dfs_up(node: int, parent: int, parent_state: any):

            # 当前节点的所有子节点状态

            child_states = [down_state[child] for child in self.children[node] 

                          if child != parent]

            

            # 合并得到当前节点状态

            result[node] = merge(node, parent_state, child_states)

            

            # 传递给每个子节点

            for child in self.children[node]:

                if child != parent:

                    # 计算子节点从父节点获得的状态

                    child_parent_state = propagate(node, result[node], child, child_states)

                    dfs_up(child, node, child_parent_state)

        

        # 根节点的父状态是初始状态

        root_init = init_state(self.root)

        dfs_up(self.root, -1, root_init)

        

        return result





def tree_diameter(n: int, edges: List[Tuple[int, int]]) -> Tuple[int, List[int]]:

    """

    求树的直径和路径

    

    树的直径：树中任意两个节点之间距离的最大值

    

    方法：两次DFS/BFS

    1. 从任意节点A出发，找到最远节点B

    2. 从B出发，找到最远节点C，B到C的距离即为直径

    

    Args:

        n: 节点数

        edges: 边列表 [(u, v), ...]

    

    Returns:

        (直径长度, 直径路径节点列表)

    """

    if n == 1:

        return (0, [0])

    

    # 构建邻接表

    adj = defaultdict(list)

    for u, v in edges:

        adj[u].append(v)

        adj[v].append(u)

    

    def bfs(start: int) -> Tuple[int, List[int]]:

        """从start出发的BFS，返回最远节点和路径"""

        from collections import deque

        

        parent = [-1] * n

        dist = [-1] * n

        queue = deque([start])

        dist[start] = 0

        last_node = start

        

        while queue:

            node = queue.popleft()

            last_node = node

            for neighbor in adj[node]:

                if dist[neighbor] == -1:

                    dist[neighbor] = dist[node] + 1

                    parent[neighbor] = node

                    queue.append(neighbor)

        

        # 重建路径

        path = []

        curr = last_node

        while curr != -1:

            path.append(curr)

            curr = parent[curr]

        path.reverse()

        

        return (last_node, path)

    

    # 第一次BFS

    farthest, _ = bfs(0)

    

    # 第二次BFS，从最远节点出发

    far_node, path = bfs(farthest)

    

    return (len(path) - 1, path)





def tree_dp_max_path(n: int, edges: List[Tuple[int, int]], values: List[int]) -> int:

    """

    树形DP：求最大路径和

    

    路径可以从任意节点开始，到任意节点结束

    需要返回以每个节点为根的子树中，以该节点为端点的最大路径

    

    Args:

        n: 节点数

        edges: 边列表

        values: 每个节点的值（路径和=节点值之和）

    

    Returns:

        树中任意两个节点之间路径的最大和

    """

    adj = defaultdict(list)

    for u, v in edges:

        adj[u].append(v)

        adj[v].append(u)

    

    max_path = float('-inf')

    

    def dfs(node: int, parent: int) -> int:

        """

        返回以node为端点，向下延伸的最大路径和

        

        同时更新全局最大路径

        """

        nonlocal max_path

        

        # 单节点路径

        max_down = values[node]

        

        # 检查子节点

        for child in adj[node]:

            if child != parent:

                child_max = dfs(child, node)

                # 更新经过当前节点的路径

                max_path = max(max_path, max_down + child_max)

                max_down = max(max_down, values[node] + child_max)

        

        return max_down

    

    dfs(0, -1)

    return max_path





def reroot_tree_sum(n: int, edges: List[Tuple[int, int]], 

                    values: List[int]) -> List[int]:

    """

    换根DP：计算以每个节点为根时，子树的值之和

    

    这是一个经典的换根DP问题：

    - 第一次DFS计算以根为端点的子树和

    - 第二次DFS通过换根，将父节点的信息传递给子节点

    

    Args:

        n: 节点数

        edges: 边列表

        values: 节点值

    

    Returns:

        result[i] = 以节点i为根时，子树所有节点值之和

    """

    adj = defaultdict(list)

    for u, v in edges:

        adj[u].append(v)

        adj[v].append(u)

    

    # down_sum[i] = 以i为根的子树中，所有节点值的和

    down_sum = [0] * n

    total = sum(values)

    

    def dfs_down(node: int, parent: int):

        """自底向上，计算down_sum"""

        down_sum[node] = values[node]

        for child in adj[node]:

            if child != parent:

                dfs_down(child, node)

                down_sum[node] += down_sum[child]

    

    dfs_down(0, -1)

    

    # result[i] = 以i为根时的整棵树（因为是无向树，换根后仍是整棵树）

    # 但如果我们考虑"子树"概念，换根会改变哪些节点属于当前根的子树

    result = [0] * n

    

    def dfs_up(node: int, parent: int, parent_contrib: int):

        """

        自顶向下，计算每个节点作为根时的结果

        

        Args:

            node: 当前节点

            parent: 父节点

            parent_contrib: 父节点传递给当前节点的贡献

        """

        # 当前节点作为根时，其"子树"是整棵树

        # 但如果我们关心的是"包含当前节点的连通分量"的大小...

        # 这里采用经典换根的定义

        result[node] = down_sum[node]

        

        for child in adj[node]:

            if child != parent:

                # 子节点从当前节点获得的信息

                # child 作为根时，其"子树"大小 = child自身 + (整树 - child的down_sum)

                child_sum = down_sum[child]

                not_child_sum = total - child_sum

                

                # 传递给子节点：子节点作为根时的大小

                dfs_up(child, node, not_child_sum)

    

    dfs_up(0, -1, 0)

    return result





class BinaryTreeDP:

    """

    二叉树上的DP模板

    

    适用于二叉树结构，状态通常定义为：

    - dp0[node] = 选择node时的最优值

    - dp1[node] = 不选择node时的最优值

    """

    

    def __init__(self, n: int):

        self.n = n

        self.left: List[int] = [-1] * n   # 左孩子

        self.right: List[int] = [-1] * n  # 右孩子

        self.val: List[int] = [0] * n     # 节点值

    

    def max_independent_set(self) -> int:

        """

        树形DP：二叉树的最大独立集

        

        独立集：集合中任意两点不相邻

        每个节点可以选择或不选择，约束是相邻节点不能同时选

        

        dp[node][0] = 不选node时，以node为根的子树的最大独立集大小

        dp[node][1] = 选node时，以node为根的子树的最大独立集大小

        

        转移：

        dp[node][0] = sum(max(dp[child][0], dp[child][1])) for child in [left, right]

        dp[node][1] = 1 + sum(dp[child][0]) for child in [left, right]

        

        Returns:

            最大独立集大小

        """

        dp0 = [0] * self.n  # 不选

        dp1 = [0] * self.n  # 选

        

        def dfs(node: int):

            if node == -1:

                return

            

            dfs(self.left[node])

            dfs(self.right[node])

            

            # 不选当前节点：子节点可以选或不选，取最大值

            take_left = max(dp0[self.left[node]], dp1[self.left[node]]) if self.left[node] != -1 else 0

            take_right = max(dp0[self.right[node]], dp1[self.right[node]]) if self.right[node] != -1 else 0

            dp0[node] = take_left + take_right

            

            # 选当前节点：子节点不能选

            not_left = dp0[self.left[node]] if self.left[node] != -1 else 0

            not_right = dp0[self.right[node]] if self.right[node] != -1 else 0

            dp1[node] = 1 + not_left + not_right

        

        dfs(0)

        return max(dp0[0], dp1[0])





if __name__ == "__main__":

    # 测试1：树的直径

    print("测试1 - 树的直径:")

    n1 = 7

    edges1 = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (2, 6)]

    diameter, path = tree_diameter(n1, edges1)

    print(f"  直径长度: {diameter}")

    print(f"  直径路径: {path}")

    

    # 测试2：最大路径和

    print("\n测试2 - 最大路径和:")

    n2 = 5

    edges2 = [(0, 1), (0, 2), (1, 3), (1, 4)]

    values2 = [1, 2, 3, 4, 5]

    max_sum = tree_dp_max_path(n2, edges2, values2)

    print(f"  最大路径和: {max_sum}")

    

    # 测试3：换根DP

    print("\n测试3 - 换根DP子树和:")

    n3 = 6

    edges3 = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5)]

    values3 = [1, 2, 3, 4, 5, 6]

    result = reroot_tree_sum(n3, edges3, values3)

    print(f"  以每个节点为根的子树和: {result}")

    

    # 测试4：最大独立集

    print("\n测试4 - 二叉树最大独立集:")

    tree = BinaryTreeDP(5)

    tree.val = [0, 1, 2, 3, 4]

    tree.left = [1, 3, 4, -1, -1]  # 0的左是1，右是2；1的左是3，右是4

    tree.right = [2, -1, -1, -1, -1]

    max_set = tree.max_independent_set()

    print(f"  最大独立集大小: {max_set}")

    

    # 测试5：TreeDP模板

    print("\n测试5 - TreeDP模板:")

    dp = TreeDP(5)

    dp.add_edge(0, 1)

    dp.add_edge(0, 2)

    dp.add_edge(1, 3)

    dp.add_edge(1, 4)

    dp.build_tree(0)

    

    result = dp.reroot_dp(

        init_state=lambda node: 1,

        merge=lambda node, state, child_states: state + sum(child_states),

        propagate=lambda parent, parent_state, child, child_states: parent_state

    )

    print(f"  每个节点作为根时的整树大小: {result}")

