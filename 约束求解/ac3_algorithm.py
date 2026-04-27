# -*- coding: utf-8 -*-
"""
算法实现：约束求解 / ac3_algorithm

本文件实现 ac3_algorithm 相关的算法功能。
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import deque


class CSPSolver:
    """
    约束满足问题求解器,使用AC-3进行弧一致性传播
    """
    
    def __init__(self, variables: List[str], domains: Dict[str, Set[int]], 
                 constraints: List[Tuple[str, str, callable]]):
        """
        初始化CSP求解器
        
        Args:
            variables: 变量列表
            domains: 每个变量的定义域 {var: {values}}
            constraints: 约束列表 [(var1, var2, allowed_pairs_function)]
        """
        self.variables = variables
        self.domains = {v: domains[v].copy() for v in variables}
        self.constraints = constraints
        
        # 构建邻居图:每个变量的邻居集合
        self.neighbors: Dict[str, Set[str]] = {v: set() for v in variables}
        for var1, var2, _ in constraints:
            self.neighbors[var1].add(var2)
            self.neighbors[var2].add(var1)
    
    def get_constraint(self, var1: str, var2: str) -> Optional[callable]:
        """
        获取两个变量之间的约束函数
        
        Args:
            var1: 变量1
            var2: 变量2
        
        Returns:
            约束函数
        """
        for v1, v2, func in self.constraints:
            if (v1 == var1 and v2 == var2) or (v1 == var2 and v2 == var1):
                return func
        return None
    
    def revise(self, var1: str, var2: str) -> bool:
        """
        Revise操作:从var1的定义域中移除与var2不相容的值
        
        Args:
            var1: 变量1
            var2: 变量2
        
        Returns:
            是否有定义域被修改
        """
        constraint = self.get_constraint(var1, var2)
        if constraint is None:
            return False
        
        revised = False
        to_remove = set()
        
        # 遍历var1的每个值
        for val1 in self.domains[var1]:
            # 检查是否存在var2的值使得约束满足
            compatible = False
            for val2 in self.domains[var2]:
                if constraint(val1, val2):
                    compatible = True
                    break
            
            # 如果没有相容的值,则移除这个值
            if not compatible:
                to_remove.add(val1)
                revised = True
        
        # 移除不相容的值
        for val in to_remove:
            self.domains[var1].remove(val)
        
        return revised
    
    def ac3(self) -> bool:
        """
        AC-3主算法:对整个CSP进行弧一致性传播
        
        Returns:
            是否所有定义域都非空
        """
        # 初始化队列:包含所有弧
        queue = deque()
        for var1, var2, _ in self.constraints:
            queue.append((var1, var2))
        
        while queue:
            var1, var2 = queue.popleft()
            
            # 对弧(var1, var2)执行Revise
            if self.revise(var1, var2):
                # 如果var1的定义域变为空,则无解
                if not self.domains[var1]:
                    return False
                
                # 将var1的所有邻居(除var2外)重新加入队列
                for var_k in self.neighbors[var1]:
                    if var_k != var2:
                        queue.append((var_k, var1))
        
        return True
    
    def backtrack(self, assignment: Dict[str, int]) -> Optional[Dict[str, int]]:
        """
        回溯搜索:在AC-3预处理后进行完整搜索
        
        Args:
            assignment: 当前部分赋值
        
        Returns:
            完整赋值或None
        """
        # 如果赋值完整,则返回
        if len(assignment) == len(self.variables):
            return assignment
        
        # 选择一个未赋值的变量(最简单的MRV启发式)
        unassigned = [v for v in self.variables if v not in assignment]
        var = min(unassigned, key=lambda v: len(self.domains[v]))
        
        for value in sorted(self.domains[var]):
            # 检查值是否与当前赋值一致
            consistent = True
            for assigned_var, assigned_val in assignment.items():
                constraint = self.get_constraint(var, assigned_var)
                if constraint and not constraint(value, assigned_val):
                    consistent = False
                    break
            
            if consistent:
                assignment[var] = value
                # 保存当前定义域快照
                saved_domains = {v: self.domains[v].copy() for v in self.variables}
                
                # 前向检查:移除其他变量中与当前赋值不一致的值
                valid = True
                for neighbor in self.neighbors[var]:
                    constraint = self.get_constraint(var, neighbor)
                    if constraint:
                        to_remove = set()
                        for n_val in self.domains[neighbor]:
                            if not constraint(value, n_val):
                                to_remove.add(n_val)
                        for rem in to_remove:
                            self.domains[neighbor].remove(rem)
                        if not self.domains[neighbor]:
                            valid = False
                            break
                
                if valid:
                    result = self.backtrack(assignment)
                    if result:
                        return result
                
                # 恢复定义域
                self.domains = saved_domains
                del assignment[var]
        
        return None
    
    def solve(self) -> Optional[Dict[str, int]]:
        """
        求解CSP:先AC-3传播,再回溯搜索
        
        Returns:
            满足所有约束的赋值或None
        """
        # 先进行AC-3弧一致性传播
        if not self.ac3():
            return None
        
        # 再进行回溯搜索
        return self.backtrack({})
    
    def solve_ac3_only(self) -> bool:
        """
        仅使用AC-3求解(不进行回溯搜索)
        用于检查弧一致性是否足以求解问题
        
        Returns:
            是否有解
        """
        return self.ac3()


def solve_coloring(variables: List[str], domains: Dict[str, Set[int]], 
                  constraints: List[Tuple[str, str, callable]]) -> Optional[Dict[str, int]]:
    """
    图着色问题求解的便捷函数
    
    Args:
        variables: 节点列表
        domains: 每节点可用颜色集合
        constraints: 边约束(相邻节点不能同色)
    
    Returns:
        着色方案或None
    """
    solver = CSPSolver(variables, domains, constraints)
    return solver.solve()


# 测试代码
if __name__ == "__main__":
    # 测试1: 简单的地图着色问题(澳大利亚地图)
    # 州: WA, NT, SA, Q, NSW, V, T
    # 相邻约束: 相邻州不能同色
    
    states = ['WA', 'NT', 'SA', 'Q', 'NSW', 'V', 'T']
    colors = {1, 2, 3, 4}  # 4种颜色
    
    domains = {state: colors.copy() for state in states}
    
    # 定义不相等约束
    def not_equal(a, b):
        return a != b
    
    constraints = [
        ('WA', 'NT', not_equal),
        ('WA', 'SA', not_equal),
        ('NT', 'SA', not_equal),
        ('NT', 'Q', not_equal),
        ('SA', 'Q', not_equal),
        ('SA', 'NSW', not_equal),
        ('SA', 'V', not_equal),
        ('Q', 'NSW', not_equal),
        ('NSW', 'V', not_equal),
    ]
    
    print("测试1 - 澳大利亚地图着色(4色):")
    solver = CSPSolver(states, domains, constraints)
    result = solver.solve()
    print(f"  结果: {result}")
    
    # 测试2: 3色着色(可能无解)
    domains_3 = {state: {1, 2, 3} for state in states}
    
    print("\n测试2 - 澳大利亚地图着色(3色):")
    solver2 = CSPSolver(states, domains_3, constraints)
    result2 = solver2.solve()
    print(f"  结果: {result2}")
    
    # 测试3: N皇后问题
    n = 8
    queens_vars = [f'Q{i}' for i in range(n)]
    queen_domain = set(range(n))  # 每行可以放在0-n-1列
    
    queen_domains = {v: queen_domain.copy() for v in queens_vars}
    
    def not_attack(pos1, pos2, offset):
        """检查两个皇后是否不攻击(同行同列同对角线)"""
        col1, col2 = pos1, pos2
        return col1 != col2 and abs(col1 - col2) != offset
    
    queen_constraints = []
    for i in range(n):
        for j in range(i + 1, n):
            offset = j - i
            queen_constraints.append((f'Q{i}', f'Q{j}', lambda p1, p2, d=offset: not_attack(p1, p2, d)))
    
    print(f"\n测试3 - {n}皇后问题:")
    solver3 = CSPSolver(queens_vars, queen_domains, queen_constraints)
    result3 = solver3.solve()
    if result3:
        # 转换为更直观的格式
        board = [['.' for _ in range(n)] for _ in range(n)]
        for var, col in result3.items():
            row = int(var[1])
            board[row][col] = 'Q'
        print("  解决方案:")
        for row in board:
            print("  " + " ".join(row))
    else:
        print("  无解")
    
    # 测试4: 数独(作为CSP问题)
    print("\n测试4 - 数独CSP求解(AC-3+回溯):")
    # 简化数独: 4x4
    cell_vars = [f'r{r}_c{c}' for r in range(4) for c in range(4)]
    cell_domains = {v: {1, 2, 3, 4} for v in cell_vars}
    
    sudoku_constraints = []
    
    # 行约束
    for r in range(4):
        for c1 in range(4):
            for c2 in range(c1 + 1, 4):
                sudoku_constraints.append((f'r{r}_c{c1}', f'r{r}_c{c2}', not_equal))
    
    # 列约束
    for c in range(4):
        for r1 in range(4):
            for r2 in range(r1 + 1, 4):
                sudoku_constraints.append((f'r{r1}_c{c}', f'r{r2}_c{c}', not_equal))
    
    # 宫约束(2x2)
    for box_r in range(2):
        for box_c in range(2):
            cells = [(box_r * 2 + dr, box_c * 2 + dc) for dr in range(2) for dc in range(2)]
            for i in range(len(cells)):
                for j in range(i + 1, len(cells)):
                    r1, c1 = cells[i]
                    r2, c2 = cells[j]
                    sudoku_constraints.append((f'r{r1}_c{c1}', f'r{r2}_c{c2}', not_equal))
    
    solver4 = CSPSolver(cell_vars, cell_domains, sudoku_constraints)
    result4 = solver4.solve()
    
    if result4:
        print("  解决方案:")
        for r in range(4):
            row = [str(result4[f'r{r}_c{c}']) for c in range(4)]
            print("  " + " ".join(row))
    else:
        print("  无解")
    
    print("\n所有测试完成!")
