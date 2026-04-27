# -*- coding: utf-8 -*-
"""
算法实现：04_图算法 / jump_point_search

本文件实现 jump_point_search 相关的算法功能。
"""

import heapq
from typing import List, Tuple, Set, Optional, Dict


class JumpPointSearch:
    """
    Jump Point Search 寻路算法
    
    使用8方向移动（4方向类似，省略对角线移动）
    假设格子代价：直线=1，对角线=√2
    """
    
    # 8个方向：上、下、左、右、左上、右上、左下、右下
    # 每个方向 (dx, dy)
    DIRECTIONS = [
        (-1, 0),   # 上
        (1, 0),    # 下
        (0, -1),   # 左
        (0, 1),    # 右
        (-1, -1),  # 左上
        (-1, 1),   # 右上
        (1, -1),   # 左下
        (1, 1),    # 右下
    ]
    
    def __init__(self, grid: List[List[int]]):
        """
        Args:
            grid: 2D网格，0=可通过，1=障碍物
        """
        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0]) if self.rows > 0 else 0
    
    def is_valid(self, x: int, y: int) -> bool:
        """检查坐标是否在网格范围内且可通过"""
        return 0 <= x < self.rows and 0 <= y < self.cols and self.grid[x][y] == 0
    
    def get_neighbors(self, x: int, y: int, 
                     parent_x: Optional[int], 
                     parent_y: Optional[int]) -> List[Tuple[int, int]]:
        """
        获取强制邻居（Pruned Neighbors）
        
        只返回从当前节点必须探索的方向，跳过明显不是最优的方向。
        这是 JPS 的核心剪枝逻辑。
        
        Args:
            x, y: 当前节点坐标
            parent_x, parent_y: 父节点坐标（用于确定移动方向）
        
        Returns:
            强制邻居列表
        """
        neighbors = []
        
        # 计算从父节点到当前节点的移动方向
        dx = x - parent_x if parent_x is not None else 0
        dy = y - parent_y if parent_y is not None else 0
        
        # 根据移动方向确定需要检查的邻居
        # 分为两类：主方向邻居和对角线邻居
        
        if dx == 0 and dy == 0:
            # 起始节点：考虑所有8个方向
            for d_x, d_y in self.DIRECTIONS:
                nx, ny = x + d_x, y + d_y
                if self.is_valid(nx, ny):
                    neighbors.append((nx, ny))
        elif dx == 0:  # 垂直方向移动
            # 水平和垂直移动：只能沿垂直方向前进
            # 强制邻居是前后两个水平方向（如果有障碍）
            for d in [-1, 1]:
                nx, ny = x + d, y + dy
                if self.is_valid(nx, ny):
                    neighbors.append((nx, ny))
            # 对角线移动被允许但需要检查
            nx1, ny1 = x - 1, y + dy
            nx2, ny2 = x + 1, y + dy
            # 只在不能直接水平移动时考虑对角线
            if not self.is_valid(x - 1, y) and self.is_valid(nx1, ny1):
                neighbors.append((nx1, ny1))
            if not self.is_valid(x + 1, y) and self.is_valid(nx2, ny2):
                neighbors.append((nx2, ny2))
        elif dy == 0:  # 水平方向移动
            # 水平和垂直移动：只能沿水平方向前进
            for d in [-1, 1]:
                nx, ny = x + dx, y + d
                if self.is_valid(nx, ny):
                    neighbors.append((nx, ny))
            # 对角线移动检查
            if not self.is_valid(x, y - 1) and self.is_valid(x + dx, ny):
                neighbors.append((x + dx, y - 1))
            if not self.is_valid(x, y + 1) and self.is_valid(x + dx, ny):
                neighbors.append((x + dx, y + 1))
        else:  # 对角线方向移动
            # 对角线移动：主方向+两个侧面邻居
            # 主方向邻居
            nx, ny = x + dx, y + dy
            if self.is_valid(nx, ny):
                neighbors.append((nx, ny))
            # 两个侧面邻居
            for d_x, d_y in [(dx, 0), (0, dy)]:
                nx, ny = x + d_x, y + d_y
                if self.is_valid(nx, ny):
                    neighbors.append((nx, ny))
        
        return neighbors
    
    def jump(self, x: int, y: int, 
             dx: int, dy: int) -> Optional[Tuple[int, int]]:
        """
        从当前节点沿指定方向递归跳跃，直到找到跳点或碰到障碍
        
        Args:
            x, y: 起始节点
            dx, dy: 移动方向
        
        Returns:
            跳点坐标，如果没有则返回 None
        """
        nx, ny = x + dx, y + dy
        
        # 检查是否越界或碰到障碍
        if not self.is_valid(nx, ny):
            return None
        
        # 如果是目标点，直接返回
        # 注意：目标点由外部检测，这里只负责跳跃逻辑
        
        # 如果在移动过程中遇到障碍或边界，则该方向没有跳点
        # 检查是否有强迫邻居（forced neighbors）
        # 如果发现强迫邻居，则该点成为跳点
        
        # 对于直线移动（水平或垂直）
        if dx == 0:  # 垂直移动
            # 检查上下两侧是否有障碍，形成强迫邻居
            if not self.is_valid(x - 1, ny) and self.is_valid(x - 1, y):
                return (nx, ny)
            if not self.is_valid(x + 1, ny) and self.is_valid(x + 1, y):
                return (nx, ny)
        elif dy == 0:  # 水平移动
            if not self.is_valid(nx, y - 1) and self.is_valid(x, y - 1):
                return (nx, ny)
            if not self.is_valid(nx, y + 1) and self.is_valid(x, y + 1):
                return (nx, ny)
        else:  # 对角线移动
            # 对角线方向需要检查两个侧面是否被阻塞
            # 检查 (x + dx, y) 方向的水平邻居
            if not self.is_valid(x, y + dy) and self.is_valid(x + dx, y + dy):
                return (nx, ny)
            # 检查 (x, y + dy) 方向的垂直邻居
            if not self.is_valid(x + dx, y) and self.is_valid(x + dx, y + dy):
                return (nx, ny)
        
        # 如果遇到障碍，不能继续跳
        if not self.is_valid(nx + dx, ny + dy):
            # 检查是否是跳点（但前方有障碍时不能跳）
            if not self.is_valid(nx, ny):
                return None
            # 这种情况下，如果移动被阻止，当前点不是跳点
            return None
        
        # 继续跳跃
        return self.jump(nx, ny, dx, dy)
    
    def find_path(self, start: Tuple[int, int], 
                  goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """
        寻找从起点到终点的最优路径
        
        Args:
            start: (row, col) 起始坐标
            goal: (row, col) 目标坐标
        
        Returns:
            路径坐标列表，如果没有路径则返回 None
        """
        # 边界检查
        if not self.is_valid(start[0], start[1]) or not self.is_valid(goal[0], goal[1]):
            return None
        
        if start == goal:
            return [start]
        
        # 优先队列：(f_score, counter, x, y)
        # counter 用于打破 f_score 相等时的平局
        counter = 0
        open_set = []
        
        # g_score[x][y] = 从起点到 (x,y) 的实际代价
        g_score: Dict[Tuple[int, int], float] = {start: 0}
        
        # f_score[x][y] = g_score + h(x,y)，其中 h 是启发式估计
        h = lambda x, y: abs(x - goal[0]) + abs(y - goal[1])  # 曼哈顿距离
        f_score = h(start[0], start[1])
        
        heapq.heappush(open_set, (f_score, counter, start[0], start[1]))
        counter += 1
        
        # 已访问节点集合
        closed_set: Set[Tuple[int, int]] = set()
        
        # 父节点记录
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        
        while open_set:
            # 取出 f_score 最小的节点
            _, _, x, y = heapq.heappop(open_set)
            current = (x, y)
            
            if current == goal:
                # 重建路径
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path
            
            if current in closed_set:
                continue
            closed_set.add(current)
            
            # 获取父节点
            parent = came_from.get(current)
            parent_x = parent[0] if parent else None
            parent_y = parent[1] if parent else None
            
            # 获取当前节点的邻居
            for neighbor in self.get_neighbors(x, y, parent_x, parent_y):
                # 计算移动方向
                if parent:
                    dx = x - parent_x
                    dy = y - parent_y
                else:
                    dx = neighbor[0] - x
                    dy = neighbor[1] - y
                
                # 尝试跳跃找到跳点
                jump_point = self.jump(x, y, dx, dy)
                
                if jump_point:
                    jp_x, jp_y = jump_point
                    
                    # 计算代价（直线=1，对角线=√2）
                    if dx != 0 and dy != 0:  # 对角线
                        cost = 1.414
                    else:
                        cost = 1.0
                    
                    tentative_g = g_score[current] + cost
                    
                    if jp_x not in g_score or tentative_g < g_score.get((jp_x, jp_y), float('inf')):
                        g_score[(jp_x, jp_y)] = tentative_g
                        f = tentative_g + h(jp_x, jp_y)
                        heapq.heappush(open_set, (f, counter, jp_x, jp_y))
                        counter += 1
                        came_from[(jp_x, jp_y)] = current
        
        return None


def jps_pathfinder(grid: List[List[int]], 
                   start: Tuple[int, int], 
                   goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
    """
    Jump Point Search 路径搜索的便捷函数
    
    Args:
        grid: 2D网格，0=可通过，1=障碍物
        start: 起始坐标 (row, col)
        goal: 目标坐标 (row, col)
    
    Returns:
        路径坐标列表
    
    示例:
        >>> grid = [[0,0,0],[1,1,0],[0,0,0]]
        >>> path = jps_pathfinder(grid, (0,0), (2,2))
    """
    jps = JumpPointSearch(grid)
    return jps.find_path(start, goal)


if __name__ == "__main__":
    # 测试1：简单网格
    grid1 = [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 1, 1, 0],
        [0, 0, 0, 0, 0],
    ]
    
    start1 = (0, 0)
    goal1 = (4, 4)
    
    path1 = jps_pathfinder(grid1, start1, goal1)
    print("测试1 - 简单网格:")
    print(f"  起点: {start1}, 终点: {goal1}")
    print(f"  路径长度: {len(path1) if path1 else '无路径'}")
    print(f"  路径: {path1}")
    
    # 测试2：复杂障碍
    grid2 = [
        [0, 0, 0, 1, 0, 0, 0],
        [0, 1, 0, 1, 0, 1, 0],
        [0, 1, 0, 0, 0, 1, 0],
        [0, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 0],
    ]
    
    start2 = (0, 0)
    goal2 = (4, 6)
    
    path2 = jps_pathfinder(grid2, start2, goal2)
    print("\n测试2 - 复杂障碍:")
    print(f"  路径: {path2}")
    
    # 测试3：直线障碍
    grid3 = [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    
    start3 = (2, 0)
    goal3 = (2, 4)
    
    path3 = jps_pathfinder(grid3, start3, goal3)
    print("\n测试3 - 直线移动:")
    print(f"  路径: {path3}")
    
    # 可视化测试
    print("\n网格可视化:")
    for i, row in enumerate(grid1):
        line = ""
        for j, cell in enumerate(row):
            if (i, j) == start1:
                line += " S "
            elif (i, j) == goal1:
                line += " G "
            elif path1 and (i, j) in path1:
                line += " * "
            else:
                line += " . " if cell == 0 else " # "
        print(line)
