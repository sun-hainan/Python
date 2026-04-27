# -*- coding: utf-8 -*-
"""
算法实现：约束求解 / min_conflicts

本文件实现 min_conflicts 相关的算法功能。
"""

from typing import Dict, List, Set, Any, Optional
import random


class MinConflictsSolver:
    """
    最小冲突求解器
    
    属性:
        variables: 变量列表
        domains: 域字典
        constraints: 约束列表 [(var1, var2, check_func)]
    """
    
    def __init__(self, variables: List[str], domains: Dict[str, List[Any]]):
        self.variables = variables
        self.domains = {v: list(d) for v, d in domains.items()}
        self.constraints: List[Tuple[str, str, callable]] = []
        
        # 缓存邻居信息
        self.neighbors: Dict[str, List[str]] = {v: [] for v in variables}
    
    def add_constraint(self, var1: str, var2: str, check: callable):
        """添加二元约束"""
        self.constraints.append((var1, var2, check))
        self.neighbors[var1].append(var2)
        self.neighbors[var2].append(var1)
    
    def get_conflicts(self, var: str, value: Any, assignment: Dict[str, Any]) -> int:
        """
        计算将 var 设为 value 会产生的冲突数
        
        参数:
            var: 变量名
            value: 候选值
            assignment: 当前赋值
        
        返回:
            冲突数
        """
        conflicts = 0
        for neighbor in self.neighbors[var]:
            if neighbor in assignment:
                # 检查与邻居的约束
                for v1, v2, check in self.constraints:
                    if (v1 == var and v2 == neighbor) or (v1 == neighbor and v2 == var):
                        if not check(value, assignment[neighbor]):
                            conflicts += 1
                        break
        return conflicts
    
    def count_total_conflicts(self, assignment: Dict[str, Any]) -> int:
        """
        计算总冲突数
        
        参数:
            assignment: 当前赋值
        
        返回:
            冲突总数
        """
        conflicts = 0
        for var in self.variables:
            for neighbor in self.neighbors[var]:
                if neighbor in assignment:
                    # 只计算每个约束一次（var < neighbor）
                    if var < neighbor:
                        for v1, v2, check in self.constraints:
                            if (v1 == var and v2 == neighbor) or (v1 == neighbor and v2 == var):
                                if not check(assignment[var], assignment[neighbor]):
                                    conflicts += 1
                                break
        return conflicts
    
    def get_conflicted_variables(self, assignment: Dict[str, Any]) -> List[str]:
        """
        找出所有违反约束的变量
        
        参数:
            assignment: 当前赋值
        
        返回:
            冲突变量列表
        """
        conflicted = set()
        
        for var in self.variables:
            for neighbor in self.neighbors[var]:
                if neighbor in assignment:
                    if var < neighbor:
                        for v1, v2, check in self.constraints:
                            if (v1 == var and v2 == neighbor) or (v1 == neighbor and v2 == var):
                                if not check(assignment[var], assignment[neighbor]):
                                    conflicted.add(var)
                                    conflicted.add(neighbor)
                                break
        return list(conflicted)
    
    def solve(self, max_steps: int = 100000, random_seed: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        最小冲突主算法
        
        参数:
            max_steps: 最大步数
            random_seed: 随机种子
        
        返回:
            完整赋值或 None
        """
        if random_seed is not None:
            random.seed(random_seed)
        
        # 步骤1：随机初始化完整赋值
        assignment = {}
        for var in self.variables:
            assignment[var] = random.choice(self.domains[var])
        
        # 步骤2：迭代改进
        for step in range(max_steps):
            # 找出冲突的变量
            conflicted = self.get_conflicted_variables(assignment)
            
            if not conflicted:
                return assignment  # 无冲突，找到解
            
            # 随机选择一个冲突变量
            var = random.choice(conflicted)
            
            # 找到最小冲突值
            min_conflicts = float('inf')
            best_value = assignment[var]
            
            for value in self.domains[var]:
                conflicts = self.get_conflicts(var, value, assignment)
                if conflicts < min_conflicts:
                    min_conflicts = conflicts
                    best_value = value
            
            # 更新赋值
            assignment[var] = best_value
            
            # 可选：打印进度
            if step % 10000 == 0:
                total = self.count_total_conflicts(assignment)
                print(f"  步骤 {step}: {total} 个冲突")
        
        return None  # 超时


# ============ 专门问题求解器 ============

def solve_n_queens(n: int, max_steps: int = 100000, random_seed: Optional[int] = None) -> Optional[List[int]]:
    """
    使用最小冲突求解 N 皇后问题
    
    参数:
        n: 皇后数量
        max_steps: 最大步数
        random_seed: 随机种子
    
    返回:
        解：每行皇后所在的列索引列表
    """
    if random_seed is not None:
        random.seed(random_seed)
    
    # 变量：每行的皇后位置
    variables = [f"Q{i}" for i in range(n)]
    domains = {v: list(range(n)) for v in variables}
    
    solver = MinConflictsSolver(variables, domains)
    
    # 添加约束：同一列、同一对角线不能有皇后
    for i in range(n):
        for j in range(i + 1, n):
            # 同一列约束
            solver.add_constraint(f"Q{i}", f"Q{j}", lambda a, b: a != b)
            
            # 对角线约束 |row1 - row2| != |col1 - col2|
            solver.add_constraint(
                f"Q{i}", f"Q{j}",
                lambda a, b: abs(i - j) != abs(a - b)
            )
    
    result = solver.solve(max_steps, random_seed)
    
    if result:
        return [result[f"Q{i}"] for i in range(n)]
    return None


def solve_sudoku(board: List[List[int]], max_steps: int = 100000) -> Optional[List[List[int]]]:
    """
    使用最小冲突求解数独
    
    参数:
        board: 9x9 棋盘，0 表示空格
        max_steps: 最大步数
    
    返回:
        解棋盘或 None
    """
    variables = []
    fixed_values: Dict[str, int] = {}
    
    # 初始化变量
    for row in range(9):
        for col in range(9):
            var = f"R{row}C{col}"
            variables.append(var)
            
            if board[row][col] != 0:
                fixed_values[var] = board[row][col]
    
    domains = {v: list(range(1, 10)) for v in variables}
    
    solver = MinConflictsSolver(variables, domains)
    
    # 行约束
    for row in range(9):
        for col1 in range(9):
            for col2 in range(col1 + 1, 9):
                solver.add_constraint(
                    f"R{row}C{col1}", f"R{row}C{col2}",
                    lambda a, b: a != b
                )
    
    # 列约束
    for col in range(9):
        for row1 in range(9):
            for row2 in range(row1 + 1, 9):
                solver.add_constraint(
                    f"R{row1}C{col}", f"R{row2}C{col}",
                    lambda a, b: a != b
                )
    
    # 3x3 宫约束
    for box_row in range(3):
        for box_col in range(3):
            cells = []
            for r in range(box_row * 3, box_row * 3 + 3):
                for c in range(box_col * 3, box_col * 3 + 3):
                    cells.append((r, c))
            
            for i in range(len(cells)):
                for j in range(i + 1, len(cells)):
                    r1, c1 = cells[i]
                    r2, c2 = cells[j]
                    solver.add_constraint(
                        f"R{r1}C{c1}", f"R{r2}C{c2}",
                        lambda a, b: a != b
                    )
    
    # 初始化固定值
    assignment = {}
    for var, val in fixed_values.items():
        assignment[var] = val
    
    # 随机初始化其他变量
    import random
    for var in variables:
        if var not in assignment:
            assignment[var] = random.choice(domains[var])
    
    # 迭代改进
    from typing import Tuple, List
    
    def get_conflicts(var: str, value: int, assign: Dict[str, int]) -> int:
        conflicts = 0
        row = int(var[1])
        col = int(var[3])
        box_row, box_col = row // 3, col // 3
        
        for other_var, other_val in assign.items():
            if other_var == var or other_val != value:
                continue
            
            other_row = int(other_var[1])
            other_col = int(other_var[3])
            
            # 同一行
            if other_row == row and other_col != col:
                conflicts += 1
            # 同一列
            if other_col == col and other_row != row:
                conflicts += 1
            # 同一宫
            if other_row // 3 == box_row and other_col // 3 == box_col:
                if other_row != row or other_col != col:
                    conflicts += 1
        
        return conflicts
    
    def get_conflicted_cells(assign: Dict[str, int]) -> List[str]:
        conflicted = []
        for var in variables:
            if get_conflicts(var, assign[var], assign) > 0:
                conflicted.append(var)
        return conflicted
    
    for step in range(max_steps):
        conflicted = get_conflicted_cells(assignment)
        
        if not conflicted:
            # 成功，构造棋盘
            result = [[0] * 9 for _ in range(9)]
            for var, val in assignment.items():
                row = int(var[1])
                col = int(var[3])
                result[row][col] = val
            return result
        
        # 随机选择冲突格子
        var = random.choice(conflicted)
        
        # 找最小冲突值
        min_conflicts = float('inf')
        best_val = assignment[var]
        
        for val in domains[var]:
            conflicts = get_conflicts(var, val, assignment)
            if conflicts < min_conflicts:
                min_conflicts = conflicts
                best_val = val
        
        assignment[var] = best_val
    
    return None


if __name__ == "__main__":
    print("=" * 60)
    print("测试1 - N 皇后 (8皇后)")
    print("=" * 60)
    
    for n in [8, 20, 50]:
        result = solve_n_queens(n, random_seed=42)
        if result:
            print(f"  {n}皇后: 找到解")
            if n <= 20:
                board = [["." for _ in range(n)] for _ in range(n)]
                for col in range(n):
                    board[result[col]][col] = "Q"
                for row in board:
                    print("    " + " ".join(row))
        else:
            print(f"  {n}皇后: 未找到解")
        print()
    
    print("=" * 60)
    print("测试2 - 数独")
    print("=" * 60)
    
    sudoku_board = [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9]
    ]
    
    result = solve_sudoku(sudoku_board)
    
    if result:
        print("  解:")
        for row in result:
            print("    " + " ".join(str(v) for v in row))
    else:
        print("  未找到解")
    
    print()
    print("=" * 60)
    print("复杂度分析:")
    print("=" * 60)
    print("  时间复杂度: O(k × m)")
    print("    k = 最大步数")
    print("    m = 约束数")
    print("  空间复杂度: O(n)")
    print("  优势: 无需搜索，直接改进")
    print("  适用: 有明确解结构的问题")
