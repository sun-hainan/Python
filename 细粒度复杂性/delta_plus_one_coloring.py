# -*- coding: utf-8 -*-

"""

算法实现：细粒度复杂性 / delta_plus_one_coloring



本文件实现 delta_plus_one_coloring 相关的算法功能。

"""



from typing import List, Set, Tuple, Optional

import random





class Graph:

    """图的简单表示"""

    def __init__(self, n: int):

        self.n = n

        self.adj: List[List[int]] = [[] for _ in range(n)]

    

    def add_edge(self, u: int, v: int):

        """添加无向边"""

        self.adj[u].append(v)

        self.adj[v].append(u)

    

    def neighbors(self, v: int) -> List[int]:

        """获取邻居"""

        return self.adj[v]

    

    def degree(self, v: int) -> int:

        """获取度数"""

        return len(self.adj[v])

    

    def max_degree(self) -> int:

        """最大度数Δ"""

        return max(self.degree(v) for v in range(self.n))





def greedy_coloring(graph: Graph) -> List[int]:

    """

    贪心着色算法:O(V+E)

    顺序给顶点着色,选择第一个可用颜色

    

    Args:

        graph: 图

    

    Returns:

        颜色数组(顶点->颜色)

    """

    n = graph.n

    colors = [-1] * n

    

    for v in range(n):

        # 邻居使用的颜色

        neighbor_colors = set(colors[u] for u in graph.neighbors(v) if colors[u] >= 0)

        

        # 选择第一个可用颜色

        c = 0

        while c in neighbor_colors:

            c += 1

        colors[v] = c

    

    return colors





def simple_distributed_coloring(graph: Graph, num_colors: int = None) -> List[int]:

    """

    简单的分布式(Δ+1)着色算法

    模拟分布式过程:每个顶点基于邻居信息独立决定颜色

    

    Args:

        graph: 图

        num_colors: 可用颜色数(默认为Δ+1)

    

    Returns:

        颜色数组

    """

    n = graph.n

    delta = graph.max_degree()

    k = num_colors if num_colors else delta + 1

    

    # 随机初始颜色

    colors = [random.randint(0, k - 1) for _ in range(n)]

    

    # 迭代改进

    changed = True

    iterations = 0

    max_iterations = n * n  # 理论上O(n²)收敛

    

    while changed and iterations < max_iterations:

        changed = False

        iterations += 1

        

        for v in range(n):

            neighbor_colors = set(colors[u] for u in graph.neighbors(v))

            current = colors[v]

            

            # 如果有邻居使用相同颜色,需要改变

            if current in neighbor_colors - {current}:

                # 选择一个邻居未使用的颜色

                used = neighbor_colors

                for c in range(k):

                    if c not in used:

                        colors[v] = c

                        changed = True

                        break

    

    return colors





def luby_coloring(graph: Graph) -> List[int]:

    """

    Luby's分布式着色算法

    使用随机化选择独立集来加速着色

    

    Args:

        graph: 图

    

    Returns:

        颜色数组

    """

    n = graph.n

    delta = graph.max_degree()

    k = delta + 1

    

    colors = [-1] * n

    remaining = set(range(n))  # 未着色顶点

    

    round_num = 0

    

    while remaining:

        round_num += 1

        new_remaining = set()

        

        # 每个未着色顶点独立决定是否尝试着色

        candidates = {}

        

        for v in remaining:

            # 计算优先级(度数越高,概率越低)

            neighbors_uncolored = sum(1 for u in graph.neighbors(v) if u in remaining)

            priority = random.random() * (neighbors_uncolored + 1)

            candidates[v] = priority

        

        # 选择局部最大优先级的顶点着色

        colored_this_round = set()

        

        for v in remaining:

            neighbors_remaining = set(graph.neighbors(v)) & remaining

            is_local_max = all(candidates[v] >= candidates[u] for u in neighbors_remaining)

            

            if is_local_max:

                # 选择一个可用颜色

                neighbor_colors = set(colors[u] for u in graph.neighbors(v) if colors[u] >= 0)

                for c in range(k):

                    if c not in neighbor_colors:

                        colors[v] = c

                        colored_this_round.add(v)

                        break

        

        # 未着色的顶点继续

        remaining -= colored_this_round

    

    return colors





def is_valid_coloring(graph: Graph, colors: List[int]) -> bool:

    """检查着色是否有效"""

    for v in range(graph.n):

        for u in graph.neighbors(v):

            if colors[v] == colors[u] and v < u:

                return False

    return True





def get_color_classes(colors: List[int]) -> List[Set[int]]:

    """获取每个颜色的顶点集合"""

    max_color = max(colors)

    classes = [set() for _ in range(max_color + 1)]

    for v, c in enumerate(colors):

        classes[c].add(v)

    return classes





# 测试代码

if __name__ == "__main__":

    random.seed(42)

    

    # 测试1: 简单图

    print("测试1 - 简单图:")

    #    0 --- 1

    #    |  X  |

    #    3 --- 2

    

    g1 = Graph(4)

    g1.add_edge(0, 1)

    g1.add_edge(1, 2)

    g1.add_edge(2, 3)

    g1.add_edge(3, 0)

    g1.add_edge(0, 2)  # 对角线

    

    colors1 = greedy_coloring(g1)

    print(f"  贪心着色: {colors1}")

    print(f"  有效: {is_valid_coloring(g1, colors1)}")

    print(f"  颜色数: {len(set(colors1))}")

    

    colors1b = simple_distributed_coloring(g1)

    print(f"  分布式着色: {colors1b}")

    print(f"  有效: {is_valid_coloring(g1, colors1b)}")

    

    # 测试2: 完全图K_n

    print("\n测试2 - 完全图K_5:")

    g2 = Graph(5)

    for i in range(5):

        for j in range(i + 1, 5):

            g2.add_edge(i, j)

    

    delta = g2.max_degree()

    print(f"  Δ={delta}, 需要Δ+1={delta+1}种颜色")

    

    colors2 = greedy_coloring(g2)

    print(f"  着色: {colors2}")

    print(f"  有效: {is_valid_coloring(g2, colors2)}")

    print(f"  颜色数: {len(set(colors2))}")

    

    # 测试3: 二分图

    print("\n测试3 - 二分图(两个完全子图):")

    g3 = Graph(6)

    # 左侧0,1,2 右侧3,4,5

    # 左侧内部全连接,右侧内部全连接,左右之间也全连接

    for i in range(3):

        for j in range(i + 1, 3):

            g3.add_edge(i, j)

    for i in range(3, 6):

        for j in range(i + 1, 6):

            g3.add_edge(i, j)

    for i in range(3):

        for j in range(3, 6):

            g3.add_edge(i, j)

    

    delta3 = g3.max_degree()

    print(f"  Δ={delta3}")

    

    colors3 = greedy_coloring(g3)

    print(f"  着色: {colors3}")

    print(f"  有效: {is_valid_coloring(g3, colors3)}")

    

    # 测试4: 随机图

    print("\n测试4 - 随机图(50顶点):")

    n = 50

    g4 = Graph(n)

    

    # G(n, p)随机图

    p = 0.1

    for i in range(n):

        for j in range(i + 1, n):

            if random.random() < p:

                g4.add_edge(i, j)

    

    delta4 = g4.max_degree()

    print(f"  Δ={delta4}")

    

    colors4 = greedy_coloring(g4)

    print(f"  贪心着色: 使用{len(set(colors4))}种颜色")

    print(f"  有效: {is_valid_coloring(g4, colors4)}")

    

    colors4b = simple_distributed_coloring(g4)

    print(f"  分布式着色: 使用{len(set(colors4b))}种颜色")

    print(f"  有效: {is_valid_coloring(g4, colors4b)}")

    

    # 测试5: 验证(Δ+1)界

    print("\n测试5 - 验证Δ+1界:")

    results = []

    for n in [20, 50, 100]:

        g = Graph(n)

        for i in range(n):

            for j in range(i + 1, n):

                if random.random() < 0.2:

                    g.add_edge(i, j)

        

        delta = g.max_degree()

        colors = greedy_coloring(g)

        max_color_used = max(colors) + 1

        

        results.append((n, delta, max_color_used, max_color_used <= delta + 1))

    

    print(f"  {'n':>5} | {'Δ':>5} | {'使用颜色':>10} | {'≤Δ+1':>8}")

    print(f"  {'-'*5}-+-{'-'*5}-+-{'-'*10}-+-{'-'*8}")

    for n, delta, used, ok in results:

        print(f"  {n:>5} | {delta:>5} | {used:>10} | {str(ok):>8}")

    

    print("\n所有测试完成!")

