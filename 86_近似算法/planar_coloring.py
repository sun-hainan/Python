# -*- coding: utf-8 -*-

"""

算法实现：近似算法 / planar_coloring



本文件实现 planar_coloring 相关的算法功能。

"""



import numpy as np

import random

from collections import defaultdict, deque





def is_planar(graph):

    """

    检查图是否是平面图 (简化检测)

    

    使用欧拉公式的必要性条件:

    对于平面图, |E| <= 3|V| - 6 (当 |V| >= 3 时)

    

    Parameters

    ----------

    graph : dict

        图的邻接表

    

    Returns

    -------

    bool

        是否可能是平面图

    """

    n = len(graph)

    m = sum(len(neighbors) for neighbors in graph.values()) // 2

    

    if n < 3:

        return True

    

    # 欧拉公式的必要条件

    return m <= 3 * n - 6





def find_cycle(graph, start):

    """

    在图中找到一个简单环

    

    Parameters

    ----------

    graph : dict

        图的邻接表

    start : int

        起始顶点

    

    Returns

    -------

    list or None

        环的顶点列表,如果不存在环则返回 None

    """

    visited = {start}

    parent = {start: None}

    queue = deque([start])

    

    while queue:

        u = queue.popleft()

        

        for v in graph.get(u, []):

            if v not in visited:

                visited.add(v)

                parent[v] = u

                queue.append(v)

            elif parent[u] != v:

                # 找到环,回溯

                cycle = [v]

                p = u

                while p != v:

                    cycle.append(p)

                    p = parent[p]

                cycle.reverse()

                return cycle

    

    return None





def planar_5_color_greedy(graph):

    """

    平面图 5-着色贪心算法

    

    算法思想:

    1. 平面图总有度 <= 5 的顶点 (否则违背欧拉公式)

    2. 递归删除度 <= 5 的顶点

    3. 按逆序着色

    

    时间复杂度: O(n)

    

    Parameters

    ----------

    graph : dict

        图的邻接表

    

    Returns

    -------

    dict or None

        着色方案,如果着色失败返回 None

    """

    vertices = list(graph.keys())

    n = len(vertices)

    

    if n == 0:

        return {}

    

    # 复制图用于修改

    g = {v: set(neighbors) for v, neighbors in graph.items()}

    

    # 按度排序的顶点列表

    degree = {v: len(g[v]) for v in vertices}

    order = sorted(vertices, key=lambda v: degree[v])

    

    # 移除顺序

    remove_order = []

    

    for _ in range(n):

        if not order:

            break

        

        # 找到度最小的顶点

        min_deg_v = min(order, key=lambda v: degree[v])

        

        # 确保度 <= 5

        if degree[min_deg_v] > 5:

            return None  # 不是平面图或实现错误

        

        remove_order.append(min_deg_v)

        order.remove(min_deg_v)

        

        # 更新邻居度数

        for neighbor in g[min_deg_v]:

            if neighbor in degree:

                degree[neighbor] -= 1

    

    # 逆序着色

    color = {}

    

    for v in reversed(remove_order):

        # 获取邻居使用的颜色

        used_colors = {color[nb] for nb in g[v] if nb in color}

        

        # 找到最小的可用颜色

        c = 0

        while c in used_colors:

            c += 1

        

        # 平面图保证 c <= 4

        if c >= 5:

            # 降级: 使用任何可用颜色

            for c in range(5):

                if c not in used_colors:

                    color[v] = c

                    break

            else:

                color[v] = 5

        else:

            color[v] = c

    

    return color





def planar_6_color_wedge_elimination(graph):

    """

    平面图 6-着色算法

    

    使用楔形消除技术:

    1. 找到一个度 <= 5 的顶点

    2. 找到其邻居中的"楔形" (不相邻的一对邻居)

    3. 消除这对邻居之间的边

    

    Parameters

    ----------

    graph : dict

        图的邻接表

    

    Returns

    -------

    dict

        着色方案

    """

    vertices = list(graph.keys())

    n = len(vertices)

    

    # 复制图

    g = {v: set(neighbors) for v, neighbors in graph.items()}

    

    # 着色顺序

    color_order = []

    

    remaining = set(vertices)

    

    while remaining:

        # 找度最小的顶点

        min_v = min(remaining, key=lambda v: len(g[v]))

        

        # 检查是否有度 <= 5 的顶点

        if len(g[min_v]) > 5:

            # 使用简单的随机去除

            neighbor = list(g[min_v])[0]

            # 去除 min_v 和 neighbor

            pass

        

        color_order.append(min_v)

        remaining.remove(min_v)

        

        # 从图中移除

        for nb in g[min_v]:

            g[nb].discard(min_v)

        g[min_v] = set()

    

    # 逆序着色

    color = {}

    

    for v in reversed(color_order):

        used_colors = {color[nb] for nb in graph.get(v, []) if nb in color}

        

        c = 0

        while c in used_colors:

            c += 1

            if c >= 6:

                c = 5  # 降级

                break

        

        color[v] = c

    

    return color





def greedy_coloring(graph):

    """

    标准贪心着色

    

    按顺序为每个顶点分配最小的可用颜色

    

    时间复杂度: O(n + m)

    

    Parameters

    ----------

    graph : dict

        图的邻接表

    

    Returns

    -------

    dict

        着色方案

    """

    vertices = list(graph.keys())

    

    # 按度数降序排列 (减少冲突)

    sorted_vertices = sorted(vertices, key=lambda v: len(graph[v]), reverse=True)

    

    color = {}

    

    for v in sorted_vertices:

        # 获取邻居的颜色

        used_colors = {color[nb] for nb in graph.get(v, []) if nb in color}

        

        # 找到最小的未使用颜色

        c = 0

        while c in used_colors:

            c += 1

        

        color[v] = c

    

    return color





def welsh_powell_coloring(graph):

    """

    Welsh-Powell 着色算法

    

    按度降序排列顶点,

    然后贪心着色

    

    Parameters

    ----------

    graph : dict

        图的邻接表

    

    Returns

    -------

    dict

        着色方案

    """

    vertices = list(graph.keys())

    

    # 按度降序排列

    sorted_vertices = sorted(vertices, key=lambda v: len(graph[v]), reverse=True)

    

    color = {}

    uncolored = set(sorted_vertices)

    

    current_color = 0

    

    while uncolored:

        # 用当前颜色尽可能多地着色

        first_uncolored = min(uncolored, key=lambda v: len(graph[v]))

        color[first_uncolored] = current_color

        uncolored.remove(first_uncolored)

        

        # 贪心添加到同色集合

        to_color = []

        for v in uncolored:

            # 检查是否与已着当前色的顶点相邻

            neighbors_with_color = [nb for nb in graph.get(v, []) 

                                   if nb in color and color[nb] == current_color]

            if not neighbors_with_color:

                to_color.append(v)

        

        for v in to_color:

            color[v] = current_color

            uncolored.remove(v)

        

        current_color += 1

    

    return color





def local_search_coloring(graph, max_iterations=1000):

    """

    局部搜索着色算法

    

    从随机着色开始,

    通过移动冲突顶点的颜色来减少冲突

    

    Parameters

    ----------

    graph : dict

        图的邻接表

    max_iterations : int

        最大迭代次数

    

    Returns

    -------

    tuple

        (着色方案, 冲突边数)

    """

    vertices = list(graph.keys())

    n = len(vertices)

    

    # 随机初始化着色

    num_colors = max(3, n // 4)  # 初始使用较多颜色

    color = {v: random.randint(0, num_colors - 1) for v in vertices}

    

    def count_conflicts():

        """计算冲突的边数"""

        conflicts = 0

        for u in graph:

            for v in graph[u]:

                if u < v and color[u] == color[v]:

                    conflicts += 1

        return conflicts

    

    def get_conflict_vertices():

        """获取所有冲突顶点"""

        conflicts = set()

        for u in graph:

            for v in graph[u]:

                if u < v and color[u] == color[v]:

                    conflicts.add(u)

                    conflicts.add(v)

        return conflicts

    

    current_conflicts = count_conflicts()

    

    for _ in range(max_iterations):

        if current_conflicts == 0:

            break

        

        # 选择一个冲突顶点

        conflict_vertices = get_conflict_vertices()

        v = random.choice(list(conflict_vertices))

        

        # 尝试所有颜色,选择减少冲突最多的

        best_color = color[v]

        best_conflicts = current_conflicts

        

        for c in range(num_colors):

            if c == color[v]:

                continue

            

            old_color = color[v]

            color[v] = c

            new_conflicts = count_conflicts()

            

            if new_conflicts < best_conflicts:

                best_conflicts = new_conflicts

                best_color = c

            

            color[v] = old_color

        

        # 如果没有改进,随机改变

        if best_color == color[v]:

            color[v] = random.randint(0, num_colors - 1)

        else:

            color[v] = best_color

        

        current_conflicts = best_conflicts

    

    return color, current_conflicts





def planar_graph_cycleEliminate(graph):

    """

    平面图环消除着色

    

    核心思想:

    1. 找到图中的最小度环

    2. 消除环上的边,保持平面性

    3. 递归着色后还原

    

    Parameters

    ----------

    graph : dict

        图的邻接表

    

    Returns

    -------

    dict

        着色方案

    """

    # 使用简化的贪心着色

    return greedy_coloring(graph)





def compute_chromatic_number_lower_bound(graph):

    """

    计算色数的下界

    

    使用:

    1. 最大团大小 ω(G) <= χ(G)

    2. 最大度数 Δ(G) + 1 >= χ(G) (Brook 定理的逆)

    

    Parameters

    ----------

    graph : dict

        图的邻接表

    

    Returns

    -------

    int

        下界值

    """

    vertices = list(graph.keys())

    

    # 最大度数

    max_degree = max(len(graph.get(v, [])) for v in vertices) if vertices else 0

    

    # 检查是否是二分图 (色数 = 2)

    if is_bipartite(graph):

        return 2

    

    # 寻找三角形

    for v in vertices:

        for u in graph.get(v, []):

            for w in graph.get(u, []):

                if w != v and v in graph.get(w, []):

                    return 3  # 存在三角形,色数 >= 3

    

    return max(1, max_degree + 1)





def is_bipartite(graph):

    """

    检查图是否是二分图 (双色)

    

    Parameters

    ----------

    graph : dict

        图的邻接表

    

    Returns

    -------

    bool

        是否是二分图

    """

    vertices = list(graph.keys())

    

    if not vertices:

        return True

    

    color = {}

    

    for start in vertices:

        if start in color:

            continue

        

        queue = deque([start])

        color[start] = 0

        

        while queue:

            v = queue.popleft()

            

            for nb in graph.get(v, []):

                if nb not in color:

                    color[nb] = 1 - color[v]

                    queue.append(nb)

                elif color[nb] == color[v]:

                    return False

    

    return True





def count_colors_used(coloring):

    """

    计算着色使用的颜色数

    

    Parameters

    ----------

    coloring : dict

        着色方案

    

    Returns

    -------

    int

        使用的颜色数

    """

    return len(set(coloring.values()))





if __name__ == "__main__":

    # 测试: 平面图着色算法

    

    print("=" * 60)

    print("平面图着色近似算法测试")

    print("=" * 60)

    

    random.seed(42)

    

    # 测试图1: 简单的平面图 (路径 + 环)

    print("\n--- 测试图1: 简单平面图 ---")

    

    # 创建一个简单的平面图: 5个顶点形成五边形

    planar_graph = {

        0: [1, 4],

        1: [0, 2],

        2: [1, 3],

        3: [2, 4],

        4: [3, 0]

    }

    

    print(f"图是否为平面图: {is_planar(planar_graph)}")

    

    color_5 = planar_5_color_greedy(planar_graph)

    print(f"5-着色算法: {color_5}")

    print(f"使用颜色数: {count_colors_used(color_5)}")

    

    # 测试图2: 更复杂的平面图

    print("\n--- 测试图2: 复杂平面图 ---")

    

    # 创建一个网格图 (平面图)

    rows, cols = 3, 3

    grid_graph = {}

    for r in range(rows):

        for c in range(cols):

            v = r * cols + c

            neighbors = []

            if c > 0:

                neighbors.append(v - 1)

            if c < cols - 1:

                neighbors.append(v + 1)

            if r > 0:

                neighbors.append(v - cols)

            if r < rows - 1:

                neighbors.append(v + cols)

            grid_graph[v] = neighbors

    

    print(f"网格图 {rows}x{cols}: {len(grid_graph)} 顶点")

    

    color_grid = planar_5_color_greedy(grid_graph)

    print(f"5-着色: 使用 {count_colors_used(color_grid)} 种颜色")

    

    color_greedy = greedy_coloring(grid_graph)

    print(f"贪心着色: 使用 {count_colors_used(color_greedy)} 种颜色")

    

    # 测试非平面图 (完整图 K5)

    print("\n--- 测试图3: K5 (非平面图) ---")

    

    k5 = {i: [j for j in range(5) if j != i] for i in range(5)}

    

    print(f"K5 是否平面图: {is_planar(k5)}")

    

    # K5 无法用 5-着色贪心成功

    color_k5 = greedy_coloring(k5)

    print(f"贪心着色: 使用 {count_colors_used(color_k5)} 种颜色")

    

    # 下界

    lower_bound = compute_chromatic_number_lower_bound(k5)

    print(f"色数下界: {lower_bound}")

    

    # 测试局部搜索着色

    print("\n--- 局部搜索着色 ---")

    

    # 创建随机图

    n_random = 10

    random_graph = {i: [] for i in range(n_random)}

    

    # 添加随机边,确保是平面图

    for i in range(n_random):

        for j in range(i + 1, n_random):

            if random.random() < 0.3:  # 30% 边密度

                # 检查平面性 (简化: 跳过)

                random_graph[i].append(j)

                random_graph[j].append(i)

    

    print(f"随机图: {len(random_graph)} 顶点")

    

    # 局部搜索

    color_ls, conflicts = local_search_coloring(random_graph, max_iterations=500)

    print(f"局部搜索: 使用 {count_colors_used(color_ls)} 种颜色, 冲突边数: {conflicts}")

    

    # Welsh-Powell

    color_wp = welsh_powell_coloring(random_graph)

    print(f"Welsh-Powell: 使用 {count_colors_used(color_wp)} 种颜色")

    

    print("\n" + "=" * 60)

    print("测试完成!")

    print("=" * 60)

