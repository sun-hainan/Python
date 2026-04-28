"""
图着色近似算法 (Graph Coloring Approximation)
============================================
图的着色问题：将节点分配颜色，使得相邻节点颜色不同。

判定问题：是否有k-着色（NP完全）
优化问题：找最小着色数（NP难）

实现多种近似算法：
- 贪婪着色
- Welsh-Powell算法
- 带回溯的贪婪着色
- 基于独立集的着色

参考：
    - Welsh, D.J.A. & Powell, M.B. (1967). An upper bound for the chromatic number.
"""

from typing import List, Dict, Set, Optional, Tuple
import random


class Graph:
    """无向图"""
    def __init__(self, n: int = 0):
        self.n = n
        self.adj = [set() for _ in range(n)]
    
    def add_edge(self, u: int, v: int):
        self.adj[u].add(v)
        self.adj[v].add(u)
    
    def neighbors(self, u: int) -> Set[int]:
        return self.adj[u]
    
    def degree(self, u: int) -> int:
        return len(self.adj[u])


def greedy_coloring(graph: Graph, order: Optional[List[int]] = None) -> Tuple[int, List[int]]:
    """
    朴素贪婪着色
    
    按给定顺序遍历节点，为每个节点分配最小的可用颜色
    
    参数:
        graph: 输入图
        order: 节点着色顺序（None表示0,1,2,...）
    
    返回:
        (使用的颜色数, 每个节点的颜色)
    """
    n = graph.n
    
    if order is None:
        order = list(range(n))
    
    colors = [-1] * n
    max_color = 0
    
    for u in order:
        # 找邻居使用的颜色
        used_colors = set()
        for v in graph.neighbors(u):
            if colors[v] != -1:
                used_colors.add(colors[v])
        
        # 分配最小可用颜色
        for c in range(max_color + 1):
            if c not in used_colors:
                colors[u] = c
                break
        else:
            # 没有可用颜色，创建新颜色
            colors[u] = max_color
            max_color += 1
    
    return max_color + 1, colors


def welsh_powell_coloring(graph: Graph) -> Tuple[int, List[int]]:
    """
    Welsh-Powell算法：按度递减顺序着色
    
    参数:
        graph: 输入图
    
    返回:
        (使用的颜色数, 每个节点的颜色)
    """
    n = graph.n
    
    # 按度降序排列节点
    order = sorted(range(n), key=lambda x: graph.degree(x), reverse=True)
    
    return greedy_coloring(graph, order)


def smallest_last_coloring(graph: Graph) -> Tuple[int, List[int]]:
    """
    Smallest Last Ordering (SL) 算法
    
    每次选择剩余节点中度最小的节点放到最后
    
    参数:
        graph: 输入图
    
    返回:
        (使用的颜色数, 每个节点的颜色)
    """
    n = graph.n
    
    # 复制邻接表和度数
    degrees = [graph.degree(i) for i in range(n)]
    neighbors = [set(graph.neighbors(i)) for i in range(n)]
    
    remaining = set(range(n))
    order = []  # 最后着色顺序
    
    for _ in range(n):
        # 选择度最小的节点
        min_deg = min(degrees[i] for i in remaining)
        candidates = [i for i in remaining if degrees[i] == min_deg]
        u = min(candidates)  # 选择编号最小的
        
        order.append(u)
        remaining.remove(u)
        
        # 更新邻居的度数
        for v in neighbors[u]:
            if v in remaining:
                degrees[v] -= 1
    
    # 反转顺序（最先移除的最后着色）
    order.reverse()
    
    return greedy_coloring(graph, order)


def dsatur_coloring(graph: Graph) -> Tuple[int, List[int]]:
    """
    DSatur (Degree of Saturation) 算法
    
    每次选择"饱和度"最高的节点着色
    饱和度 = 已着色邻居使用的不同颜色数
    
    参数:
        graph: 输入图
    
    返回:
        (使用的颜色数, 每个节点的颜色)
    """
    n = graph.n
    
    colors = [-1] * n
    saturation = [0] * n  # 饱和度
    neighbor_colors = [set() for _ in range(n)]  # 邻居使用的颜色
    
    # 初始化：所有节点未着色，饱和度为0
    
    def get_saturation(u: int) -> Tuple[int, int]:
        """返回(饱和度, 度数)用于比较"""
        return saturation[u], graph.degree(u)
    
    colored_count = 0
    max_color = 0
    
    while colored_count < n:
        # 选择饱和度最高（且在平局时度最高）的未着色节点
        candidates = [u for u in range(n) if colors[u] == -1]
        candidates.sort(key=get_saturation, reverse=True)
        
        u = candidates[0]
        
        # 找最小可用颜色
        available = set(range(max_color + 1)) - neighbor_colors[u]
        if not available:
            available.add(max_color)
        
        c = min(available)
        colors[u] = c
        
        if c == max_color:
            max_color += 1
        
        colored_count += 1
        
        # 更新邻居的饱和度和颜色集
        for v in graph.neighbors(u):
            neighbor_colors[v].add(c)
            # 重新计算v的饱和度
            sat = len(neighbor_colors[v])
            saturation[v] = sat
    
    return max_color, colors


def backtrack_coloring(graph: Graph, max_colors: int, 
                       order: Optional[List[int]] = None) -> Optional[List[int]]:
    """
    带回溯的完全搜索（用于小图）
    
    参数:
        graph: 输入图
        max_colors: 最大允许颜色数
        order: 着色顺序
    
    返回:
        着色方案或None（如果不可能）
    """
    n = graph.n
    
    if order is None:
        order = list(range(n))
    
    colors = [-1] * n
    
    def is_safe(u: int, c: int) -> bool:
        """检查给节点u着颜色c是否安全"""
        for v in graph.neighbors(u):
            if colors[v] == c:
                return False
        return True
    
    def backtrack(idx: int) -> bool:
        if idx == n:
            return True
        
        u = order[idx]
        for c in range(max_colors):
            if is_safe(u, c):
                colors[u] = c
                if backtrack(idx + 1):
                    return True
                colors[u] = -1
        
        return False
    
    if backtrack(0):
        return colors
    return None


def independent_set_coloring(graph: Graph) -> Tuple[int, List[int]]:
    """
    基于最大独立集的着色算法
    
    思路：每次找一个最大独立集，分配一种颜色，删除这些节点，重复
    
    参数:
        graph: 输入图
    
    返回:
        (使用的颜色数, 每个节点的颜色)
    """
    n = graph.n
    
    colors = [-1] * n
    remaining = set(range(n))
    color = 0
    
    while remaining:
        # 贪心找独立集：按度升序选择节点
        independent_set = set()
        current_remaining = remaining.copy()
        
        while current_remaining:
            # 选择度最小的节点
            degrees = {u: len(graph.neighbors(u) & current_remaining) for u in current_remaining}
            u = min(degrees, key=degrees.get)
            
            independent_set.add(u)
            # 删除u及其邻居
            to_remove = {u} | graph.neighbors(u)
            current_remaining -= to_remove
        
        # 给独立集着色
        for u in independent_set:
            colors[u] = color
            remaining.remove(u)
        
        color += 1
    
    return color, colors


def is_proper_coloring(graph: Graph, colors: List[int]) -> bool:
    """检查着色是否合法"""
    for u in range(graph.n):
        for v in graph.neighbors(u):
            if colors[u] == colors[v]:
                return False
    return True


def chromatic_number_bounds(graph: Graph) -> Tuple[int, int]:
    """
    计算色数的界
    
    返回:
        (下界, 上界)
    """
    n = graph.n
    
    # 上界：SL着色数
    upper, _ = smallest_last_coloring(graph)
    
    # 下界：最大 clique 大小 或 max degree + 1
    max_deg = max(graph.degree(i) for i in range(n))
    lower = max_deg + 1
    
    # 更紧的下界：邻接节点度的最大值
    for u in range(n):
        neighbor_deg_sum = sum(graph.degree(v) for v in graph.neighbors(u))
        lower = max(lower, neighbor_deg_sum // graph.degree(u) + 1 if graph.degree(u) > 0 else 1)
    
    return lower, upper


if __name__ == "__main__":
    print("=== 图着色近似算法测试 ===")
    
    # 测试图1: 奇环 C5
    g1 = Graph(5)
    for i in range(5):
        g1.add_edge(i, (i + 1) % 5)
    
    print("\nC5 (5-环):")
    print(f"色数界: {chromatic_number_bounds(g1)}")
    
    colors_gp, _ = greedy_coloring(g1)
    print(f"朴素贪婪着色: {colors_gp} 色")
    
    colors_wp, _ = welsh_powell_coloring(g1)
    print(f"Welsh-Powell: {colors_wp} 色")
    
    colors_ds, colors_ds_vals = dsatur_coloring(g1)
    print(f"DSatur: {colors_ds} 色, 着色: {colors_ds_vals}")
    
    # 测试图2: 完全图 K4
    g2 = Graph(4)
    for i in range(4):
        for j in range(i + 1, 4):
            g2.add_edge(i, j)
    
    print("\n\n完全图 K4:")
    print(f"色数界: {chromatic_number_bounds(g2)}")
    
    colors_k4, _ = dsatur_coloring(g2)
    print(f"DSatur: {colors_k4} 色")
    
    # 测试图3: 二分图（偶环）
    g3 = Graph(6)
    for i in range(6):
        g3.add_edge(i, (i + 1) % 6)
    
    print("\n\nC6 (6-环, 二分图):")
    print(f"色数界: {chromatic_number_bounds(g3)}")
    
    colors_c6, c6_colors = dsatur_coloring(g3)
    print(f"DSatur: {colors_c6} 色")
    print(f"着色方案: {c6_colors}")
    print(f"合法着色: {is_proper_coloring(g3, c6_colors)}")
    
    # 测试图4: 平面图示例
    g4 = Graph(5)
    g4.add_edge(0, 1)
    g4.add_edge(1, 2)
    g4.add_edge(2, 3)
    g4.add_edge(3, 4)
    g4.add_edge(4, 0)
    g4.add_edge(0, 2)  # 对角线
    g4.add_edge(1, 3)
    
    print("\n\n平面图示例:")
    colors_pl, _ = dsatur_coloring(g4)
    print(f"DSatur: {colors_pl} 色")
    
    # 测试带回溯搜索
    print("\n\n带回溯搜索 (max_colors=3):")
    result = backtrack_coloring(g3, 3)
    print(f"C6 3-着色: {'成功' if result else '失败'}")
    
    result2 = backtrack_coloring(g1, 3)
    print(f"C5 3-着色: {'成功' if result2 else '失败'}")
    
    result3 = backtrack_coloring(g1, 2)
    print(f"C5 2-着色: {'成功' if result3 else '失败'}")
    
    print("\n=== 测试完成 ===")
