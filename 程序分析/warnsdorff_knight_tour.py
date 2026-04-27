# -*- coding: utf-8 -*-
"""
算法实现：程序分析 / warnsdorff_knight_tour

本文件实现 warnsdorff_knight_tour 相关的算法功能。
"""

from typing import List, Tuple, Optional, Set
from collections import defaultdict


class KnightTour:
    """
    骑士周游问题求解器
    
    使用Warnsdorff算法找出一条骑士周游路径。
    """
    
    # 骑士的8种移动方向（马字形）
    # 每个元组表示(dx, dy)：横向和纵向的位移
    MOVES = [
        (-2, -1), (-2, 1),   # 向左上方、左上方（实际上是向左跳2格，上跳1格）
        (-1, -2), (-1, 2),   # 向左上方、左上方（向左跳1格，上跳2格）
        (1, -2), (1, 2),     # 向右上方、右上方（向右跳1格，上跳2格）
        (2, -1), (2, 1),     # 向右上方、右上方（向右跳2格，上跳1格）
    ]
    # 修正：标准的骑士8方向移动
    MOVES = [
        (-2, -1), (-2, 1),
        (-1, -2), (-1, 2),
        (1, -2), (1, 2),
        (2, -1), (2, 1),
    ]
    
    def __init__(self, board_size: int):
        """
        初始化骑士周游求解器
        
        Args:
            board_size: 棋盘大小（N×N）
        """
        self.board_size = board_size
        # 棋盘：board[y][x] = step_number（访问顺序），-1表示未访问
        self.board: List[List[int]] = [[-1 for _ in range(board_size)] for _ in range(board_size)]
        # 已访问格子数
        self.visited_count = 0
        # 总格子数
        self.total_cells = board_size * board_size
        # 路径记录
        self.path: List[Tuple[int, int]] = []
    
    def reset(self):
        """重置棋盘"""
        self.board = [[-1 for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.visited_count = 0
        self.path = []
    
    def is_valid(self, x: int, y: int) -> bool:
        """
        检查坐标是否在棋盘内
        
        Args:
            x: 横坐标
            y: 纵坐标
            
        Returns:
            如果坐标有效返回True
        """
        return 0 <= x < self.board_size and 0 <= y < self.board_size
    
    def is_unvisited(self, x: int, y: int) -> bool:
        """
        检查格子是否未访问
        
        Args:
            x: 横坐标
            y: 纵坐标
            
        Returns:
            如果未访问返回True
        """
        return self.is_valid(x, y) and self.board[y][x] == -1
    
    def get_possible_moves(self, x: int, y: int) -> List[Tuple[int, int]]:
        """
        获取从(x,y)出发的所有可能移动
        
        Args:
            x: 横坐标
            y: 纵坐标
            
        Returns:
            可能移动到的坐标列表
        """
        moves = []
        for dx, dy in self.MOVES:
            nx, ny = x + dx, y + dy
            if self.is_unvisited(nx, ny):
                moves.append((nx, ny))
        return moves
    
    def count_onward_moves(self, x: int, y: int) -> int:
        """
        计算从(x,y)出发还有多少后续可能移动
        
        用于Warnsdorff规则的选择。
        
        Args:
            x: 横坐标
            y: 纵坐标
            
        Returns:
            后续可能移动数
        """
        return len(self.get_possible_moves(x, y))
    
    def warnsdorff_move(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        """
        使用Warnsdorff规则选择下一步
        
        选择所有可能移动中，后续可移动次数最少的那个。
        这样可以避免走到"死胡同"。
        
        Args:
            x: 横坐标
            y: 纵坐标
            
        Returns:
            最佳下一步坐标，如果没有可能移动则返回None
        """
        possible_moves = self.get_possible_moves(x, y)
        
        if not possible_moves:
            return None
        
        # 按后续可移动次数排序
        moves_with_counts = []
        for mx, my in possible_moves:
            count = self.count_onward_moves(mx, my)
            moves_with_counts.append((count, mx, my))
        
        # 选择后续移动最少的（Warnsdorff规则）
        moves_with_counts.sort(key=lambda t: t[0])
        
        return (moves_with_counts[0][1], moves_with_counts[0][2])
    
    def solve(self, start_x: int, start_y: int, 
              max_attempts: int = 100) -> bool:
        """
        求解骑士周游问题
        
        使用Warnsdorff算法尝试找到一条周游路径。
        
        Args:
            start_x: 起始横坐标
            start_y: 起始纵坐标
            max_attempts: 最大尝试次数（用于随机化Warnsdorff）
            
        Returns:
            如果找到解返回True
        """
        self.reset()
        
        if not self.is_valid(start_x, start_y):
            return False
        
        x, y = start_x, start_y
        
        for attempt in range(max_attempts):
            if attempt > 0:
                # 随机打乱相同最小值的移动，增加多样性
                self.reset()
                x, y = start_x, start_y
            
            while True:
                # 标记当前格子
                self.board[y][x] = self.visited_count
                self.path.append((x, y))
                self.visited_count += 1
                
                # 检查是否完成
                if self.visited_count == self.total_cells:
                    return True
                
                # 使用Warnsdorff规则选择下一步
                next_move = self.warnsdorff_move(x, y)
                
                if next_move is None:
                    # 无法继续，提前失败
                    break
                
                x, y = next_move
            
            # 本次尝试失败，重置并重试
            if attempt < max_attempts - 1:
                self.reset()
                x, y = start_x, start_y
        
        return False
    
    def get_path(self) -> List[Tuple[int, int]]:
        """
        获取周游路径
        
        Returns:
            按访问顺序排列的坐标列表
        """
        return self.path
    
    def get_board(self) -> List[List[int]]:
        """
        获取棋盘状态
        
        Returns:
            棋盘二维数组
        """
        return self.board
    
    def print_board(self):
        """打印棋盘（用于调试）"""
        size = self.board_size
        # 计算数字宽度
        width = len(str(size * size))
        
        # 打印上边框
        print(" " + "-" * (size * (width + 1) + 1))
        
        for y in range(size):
            row = "|"
            for x in range(size):
                val = self.board[y][x]
                if val == -1:
                    row += " " * width + " "
                else:
                    row += f"{val:>{width}} "
            row += "|"
            print(row)
        
        # 打印下边框
        print(" " + "-" * (size * (width + 1) + 1))


class WarnsdorffPathPlanner:
    """
    Warnsdorff路径规划器
    
    将Warnsdorff算法推广到一般图路径规划问题。
    """
    
    def __init__(self):
        """初始化路径规划器"""
        # 图的邻接表表示：node -> [neighbor_nodes]
        self.graph: Dict[int, List[int]] = defaultdict(list)
        # 节点数
        self.node_count = 0
    
    def add_edge(self, from_node: int, to_node: int):
        """
        添加图的一条边
        
        Args:
            from_node: 起始节点
            to_node: 目标节点
        """
        if from_node not in self.graph:
            self.graph[from_node] = []
        if to_node not in self.graph[from_node]:
            self.graph[from_node].append(to_node)
        self.node_count = max(self.node_count, from_node + 1, to_node + 1)
    
    def get_unvisited_neighbors(self, node: int, visited: Set[int]) -> List[int]:
        """
        获取未访问的邻居节点
        
        Args:
            node: 当前节点
            visited: 已访问节点集合
            
        Returns:
            未访问的邻居列表
        """
        return [n for n in self.graph.get(node, []) if n not in visited]
    
    def count_onward_neighbors(self, node: int, visited: Set[int]) -> int:
        """
        计算从node出发还有多少未访问邻居
        
        Args:
            node: 节点
            visited: 已访问集合
            
        Returns:
            未访问邻居数量
        """
        return len(self.get_unvisited_neighbors(node, visited))
    
    def warnsdorff_next(self, node: int, visited: Set[int]) -> Optional[int]:
        """
        使用Warnsdorff规则选择下一个节点
        
        Args:
            node: 当前节点
            visited: 已访问集合
            
        Returns:
            最佳下一节点，如果没有则返回None
        """
        neighbors = self.get_unvisited_neighbors(node, visited)
        
        if not neighbors:
            return None
        
        # 选择后续邻居最少的
        min_count = float('inf')
        best_node = None
        
        for n in neighbors:
            count = self.count_onward_neighbors(n, visited)
            if count < min_count:
                min_count = count
                best_node = n
        
        return best_node
    
    def find_path(self, start: int) -> Optional[List[int]]:
        """
        尝试找到一条经过所有节点的路径
        
        使用Warnsdorff贪心策略。
        
        Args:
            start: 起始节点
            
        Returns:
            路径节点列表，如果不存在返回None
        """
        visited: Set[int] = set()
        path = [start]
        visited.add(start)
        
        while len(visited) < self.node_count:
            next_node = self.warnsdorff_next(path[-1], visited)
            
            if next_node is None:
                # 无法继续
                return None
            
            path.append(next_node)
            visited.add(next_node)
        
        return path


if __name__ == "__main__":
    print("=" * 60)
    print("测试1：5×5棋盘的骑士周游")
    print("=" * 60)
    
    tour = KnightTour(5)
    
    # 从角落开始
    success = tour.solve(0, 0)
    
    print(f"\n求解结果: {'成功' if success else '失败'}")
    
    if success:
        print(f"\n访问路径（共{len(tour.get_path())}步）:")
        path = tour.get_path()
        # 每行显示10个坐标
        for i in range(0, len(path), 10):
            print("  " + ", ".join(f"({x},{y})" for x, y in path[i:i+10]))
        
        print("\n棋盘状态:")
        tour.print_board()
    
    print("\n" + "=" * 60)
    print("测试2：6×6棋盘的骑士周游")
    print("=" * 60)
    
    tour2 = KnightTour(6)
    success2 = tour2.solve(0, 0, max_attempts=50)
    
    print(f"\n求解结果: {'成功' if success2 else '失败'}")
    
    if success2:
        print(f"\n访问路径长度: {len(tour2.get_path())}")
        print("\n棋盘状态:")
        tour2.print_board()
    
    print("\n" + "=" * 60)
    print("测试3：一般图的Warnsdorff路径规划")
    print("=" * 60)
    
    # 创建一个简单的图
    planner = WarnsdorffPathPlanner()
    
    # 添加边（无向图）
    edges = [
        (0, 1), (0, 2), (0, 3),
        (1, 4), (1, 5),
        (2, 4), (2, 6),
        (3, 5), (3, 6),
        (4, 7), (5, 7),
        (6, 7)
    ]
    
    for from_node, to_node in edges:
        planner.add_edge(from_node, to_node)
        planner.add_edge(to_node, from_node)
    
    print("\n图结构（邻接表）:")
    for node in sorted(planner.graph.keys()):
        neighbors = sorted(planner.graph[node])
        print(f"  节点 {node}: -> {neighbors}")
    
    path = planner.find_path(0)
    
    print(f"\n从节点0开始的路径: {path if path else '未找到'}")
    print(f"路径长度: {len(path) if path else 0}")
    
    print("\nWarnsdorff算法测试完成!")
    print("\n注意：Warnsdorff算法是贪心算法，不保证一定找到解。")
    print("对于真正的周游问题，建议使用：")
    print("  1. 迭代深化搜索（IDA*）")
    print("  2. 回溯 + Warnsdorff启发式")
    print("  3. 神经网络或遗传算法优化")
