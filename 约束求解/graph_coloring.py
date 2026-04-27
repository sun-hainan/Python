# -*- coding: utf-8 -*-
"""
算法实现：约束求解 / graph_coloring

本文件实现 graph_coloring 相关的算法功能。
"""

from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict


class GraphColoringSolver:
    """
    图着色问题求解器
    使用回溯搜索配合前向检查来避免无效搜索
    """
    
    def __init__(self, num_vertices: int, edges: List[Tuple[int, int]], num_colors: int):
        """
        初始化求解器
        
        Args:
            num_vertices: 顶点数量(0到num_vertices-1)
            edges: 边列表,每条边是一个(u, v)元组
            num_colors: 可用的颜色数量(1到num_colors)
        """
        self.n = num_vertices
        self.m = num_colors
        self.edges = edges
        
        # 构建邻接表
        self.adj: Dict[int, Set[int]] = defaultdict(set)
        for u, v in edges:
            self.adj[u].add(v)
            self.adj[v].add(u)
        
        # 确保所有顶点都在邻接表中
        for i in range(num_vertices):
            if i not in self.adj:
                self.adj[i] = set()
    
    def get_neighbors(self, vertex: int) -> Set[int]:
        """获取顶点的所有邻居"""
        return self.adj[vertex]
    
    def is_safe(self, vertex: int, color: int, assignment: Dict[int, int]) -> bool:
        """
        检查将某顶点染为某颜色是否安全
        
        Args:
            vertex: 顶点
            color: 颜色
            assignment: 当前部分着色方案
        
        Returns:
            是否安全
        """
        for neighbor in self.adj[vertex]:
            if neighbor in assignment and assignment[neighbor] == color:
                return False
        return True
    
    def get_conflict_vertices(self, assignment: Dict[int, int]) -> Set[int]:
        """
        找出当前着色方案中所有有冲突的顶点
        
        Args:
            assignment: 当前着色方案
        
        Returns:
            冲突顶点集合
        """
        conflicts = set()
        for u, v in self.edges:
            if u in assignment and v in assignment and assignment[u] == assignment[v]:
                conflicts.add(u)
                conflicts.add(v)
        return conflicts
    
    def forward_check(self, vertex: int, color: int, 
                      remaining_colors: Dict[int, Set[int]]) -> Dict[int, Set[int]]:
        """
        前向检查:更新剩余可用颜色
        当给一个顶点着色后,更新其邻居的可用颜色
        
        Args:
            vertex: 被着色的顶点
            color: 颜色
            remaining_colors: 每个顶点的剩余可用颜色
        
        Returns:
            更新后的剩余可用颜色
        """
        new_remaining = {v: remaining_colors[v].copy() for v in remaining_colors}
        
        # 移除邻居的颜色color
        for neighbor in self.adj[vertex]:
            if color in new_remaining[neighbor]:
                new_remaining[neighbor].discard(color)
                # 如果邻居没有可用颜色,则失败
                if not new_remaining[neighbor]:
                    return None
        
        return new_remaining
    
    def solve_backtrack(self, vertex: int, assignment: Dict[int, int],
                        remaining_colors: Dict[int, Set[int]]) -> Optional[Dict[int, int]]:
        """
        回溯搜索
        
        Args:
            vertex: 当前要处理的顶点
            assignment: 当前着色方案
            remaining_colors: 每个顶点的剩余可用颜色
        
        Returns:
            完整着色方案或None
        """
        # 所有顶点都已着色
        if vertex == self.n:
            return assignment
        
        # 获取当前顶点的邻居(已着色)
        neighbors = self.get_neighbors(vertex)
        colored_neighbors = [n for n in neighbors if n in assignment]
        
        # 选择颜色:优先选择导致约束最少的
        available = []
        for color in range(1, self.m + 1):
            # 检查是否与邻居冲突
            conflict = False
            for neighbor in colored_neighbors:
                if assignment[neighbor] == color:
                    conflict = True
                    break
            if not conflict:
                available.append(color)
        
        # 如果没有可用颜色,回溯
        if not available:
            return None
        
        # 尝试每个可用颜色
        for color in available:
            # 着色
            assignment[vertex] = color
            
            # 前向检查
            new_remaining = self.forward_check(vertex, color, remaining_colors)
            
            if new_remaining is not None:
                # 递归处理下一个顶点
                result = self.solve_backtrack(vertex + 1, assignment, new_remaining)
                if result:
                    return result
            
            # 回溯
            del assignment[vertex]
        
        return None
    
    def solve_mrv(self, assignment: Dict[int, int],
                  remaining_colors: Dict[int, Set[int]]) -> Optional[Dict[int, int]]:
        """
        使用MRV(Minimum Remaining Values)启发式的回溯搜索
        
        Args:
            assignment: 当前着色方案
            remaining_colors: 每个顶点的剩余可用颜色
        
        Returns:
            完整着色方案或None
        """
        # 所有顶点都已着色
        if len(assignment) == self.n:
            return assignment
        
        # 选择剩余颜色最少的未着色顶点(MRV启发式)
        unassigned = [v for v in range(self.n) if v not in assignment]
        vertex = min(unassigned, key=lambda v: len(remaining_colors[v]))
        
        # 按约束程度排序颜色
        neighbors = self.get_neighbors(vertex)
        colored_neighbors = [n for n in neighbors if n in assignment]
        
        available_colors = []
        for color in remaining_colors[vertex]:
            conflict = False
            for neighbor in colored_neighbors:
                if assignment[neighbor] == color:
                    conflict = True
                    break
            if not conflict:
                available_colors.append(color)
        
        for color in available_colors:
            assignment[vertex] = color
            new_remaining = self.forward_check(vertex, color, remaining_colors)
            
            if new_remaining is not None:
                result = self.solve_mrv(assignment, new_remaining)
                if result:
                    return result
            
            del assignment[vertex]
        
        return None
    
    def solve(self, use_mrv: bool = True) -> Optional[Dict[int, int]]:
        """
        求解图着色问题
        
        Args:
            use_mrv: 是否使用MRV启发式
        
        Returns:
            着色方案或None
        """
        # 初始化每个顶点的可用颜色集合
        all_colors = set(range(1, self.m + 1))
        remaining_colors = {v: all_colors.copy() for v in range(self.n)}
        
        if use_mrv:
            return self.solve_mrv({}, remaining_colors)
        else:
            return self.solve_backtrack(0, {}, remaining_colors)
    
    def solve_greedy(self) -> Optional[Dict[int, int]]:
        """
        贪心着色(不能保证最优,但速度快)
        
        Returns:
            贪心着色方案
        """
        assignment = {}
        
        for vertex in range(self.n):
            # 获取邻居已用的颜色
            used_colors = set()
            for neighbor in self.adj[vertex]:
                if neighbor in assignment:
                    used_colors.add(assignment[neighbor])
            
            # 选择最小的可用颜色
            for color in range(1, self.m + 1):
                if color not in used_colors:
                    assignment[vertex] = color
                    break
        
        return assignment


def solve_graph_coloring(num_vertices: int, edges: List[Tuple[int, int]], 
                         num_colors: int, use_mrv: bool = True) -> Optional[Dict[int, int]]:
    """
    图着色问题求解的便捷函数
    
    Args:
        num_vertices: 顶点数量
        edges: 边列表
        num_colors: 颜色数量
        use_mrv: 是否使用MRV启发式
    
    Returns:
        着色方案或None
    """
    solver = GraphColoringSolver(num_vertices, edges, num_colors)
    return solver.solve(use_mrv)


# 测试代码
if __name__ == "__main__":
    # 测试1: 简单的4顶点完全图(需要4种颜色)
    print("测试1 - K4完全图(需要4色):")
    edges_k4 = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    result = solve_graph_coloring(4, edges_k4, 4)
    print(f"  结果: {result}")
    
    # 测试2: 同样的图只用3色(应该无解)
    print("\n测试2 - K4完全图(3色,应无解):")
    result = solve_graph_coloring(4, edges_k4, 3)
    print(f"  结果: {result}")
    
    # 测试3: 5顶点图,需要3色
    #    0 --- 1
    #    |  X  |
    #    3 --- 2
    #      \ |
    #       4
    print("\n测试3 - 复杂图:")
    edges_complex = [
        (0, 1), (0, 3),
        (1, 2), (1, 4),
        (2, 3), (2, 4),
        (3, 4)
    ]
    result = solve_graph_coloring(5, edges_complex, 3)
    print(f"  结果: {result}")
    
    # 验证结果
    if result:
        print("  验证: ", end="")
        valid = True
        for u, v in edges_complex:
            if result[u] == result[v]:
                valid = False
                print(f"边({u},{v})冲突!", end=" ")
        print("有效" if valid else "无效")
    
    # 测试4: 二分图(只需要2色)
    print("\n测试4 - 二分图(2色):")
    bipartite_edges = [
        (0, 1), (0, 3), (0, 5),
        (1, 2), (1, 4),
        (2, 3), (2, 6),
        (3, 7),
        (4, 5), (4, 7),
        (5, 6),
        (6, 7)
    ]
    result = solve_graph_coloring(8, bipartite_edges, 2)
    print(f"  结果: {result}")
    
    # 测试5: 美国地图(简化版,需要4色)
    print("\n测试5 - 简化美国地图:")
    # 简化: 7个区域
    states = ['WA', 'OR', 'CA', 'NV', 'AZ', 'NM', 'UT']
    state_edges = [
        ('WA', 'OR'), ('WA', 'CA'), ('WA', 'NV'),
        ('OR', 'CA'), ('OR', 'NV'), ('OR', 'ID'),
        ('CA', 'NV'), ('CA', 'AZ'),
        ('NV', 'AZ'), ('NV', 'UT'), ('NV', 'ID'),
        ('AZ', 'NM'), ('AZ', 'UT'),
        ('NM', 'UT'), ('NM', 'CO'), ('NM', 'OK'),
        ('UT', 'CO'), ('UT', 'ID'),
    ]
    # 转换并简化
    n = len(states)
    edges_map = []
    for s1, s2 in state_edges:
        if s1 in states and s2 in states:
            i1, i2 = states.index(s1), states.index(s2)
            edges_map.append((i1, i2))
    
    result = solve_graph_coloring(n, edges_map, 4)
    if result:
        coloring = {states[i]: c for i, c in result.items()}
        print(f"  着色方案: {coloring}")
    
    # 测试6: 贪心vs精确对比
    print("\n测试6 - 贪心 vs 精确:")
    solver = GraphColoringSolver(10, edges_complex + [(4, 0), (3, 1)], 3)
    
    greedy_result = solver.solve_greedy()
    print(f"  贪心结果: {greedy_result}")
    
    exact_result = solver.solve(use_mrv=True)
    print(f"  精确结果: {exact_result}")
    
    print("\n所有测试完成!")
