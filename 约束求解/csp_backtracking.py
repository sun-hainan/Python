# -*- coding: utf-8 -*-
"""
算法实现：约束求解 / csp_backtracking

本文件实现 csp_backtracking 相关的算法功能。
"""

from typing import List, Dict, Set, Any, Optional, Callable, Tuple
from enum import Enum


class VarOrdering(Enum):
    """变量排序策略"""
    STATIC = 1          # 静态顺序
    MRV = 2             # 最小剩余值
    DEGREE = 3          # 最大度
    MRV_DEGREE = 4      # MRV + 度启发式


class ValOrdering(Enum):
    """值排序策略"""
    STATIC = 1          # 静态顺序
    LCV = 2             # 最少约束值


class CSPSearchSolver:
    """
    带推理的通用CSP回溯求解器
    支持多种变量选择、值排序和前向检查策略
    """
    
    def __init__(self, variables: List[str], domains: Dict[str, Set[Any]], 
                 constraints: List[Tuple[str, str, Callable]]):
        """
        初始化求解器
        
        Args:
            variables: 变量列表
            domains: 变量定义域
            constraints: 二元约束列表 [(var1, var2, predicate)]
        """
        self.variables = variables
        self.domains = {v: domains[v].copy() for v in variables}
        self.constraints = constraints
        
        # 构建邻接表
        self.neighbors: Dict[str, Set[str]] = {v: set() for v in variables}
        for v1, v2, _ in constraints:
            self.neighbors[v1].add(v2)
            self.neighbors[v2].add(v1)
        
        # 策略设置
        self.var_ordering = VarOrdering.MRV
        self.val_ordering = ValOrdering.LCV
        self.forward_checking = True
        self.arc_consistency = True
        
        # 统计
        self.nodes_explored = 0
        self.max_depth = 0
    
    def get_constraint(self, var1: str, var2: str) -> Optional[Callable]:
        """获取两个变量之间的约束"""
        for v1, v2, pred in self.constraints:
            if (v1 == var1 and v2 == var2) or (v1 == var2 and v2 == var1):
                return pred
        return None
    
    def is_consistent(self, var: str, value: Any, assignment: Dict[str, Any]) -> bool:
        """
        检查将某变量设为某值是否与当前赋值一致
        
        Args:
            var: 变量
            value: 值
            assignment: 当前赋值
        
        Returns:
            是否一致
        """
        for neighbor in self.neighbors[var]:
            if neighbor in assignment:
                constraint = self.get_constraint(var, neighbor)
                if constraint and not constraint(value, assignment[neighbor]):
                    return False
        return True
    
    def select_variable(self, assignment: Dict[str, Any], 
                       remaining_domains: Dict[str, Set[Any]]) -> Optional[str]:
        """
        选择下一个要赋值的变量
        
        Args:
            assignment: 当前赋值
            remaining_domains: 每个变量的剩余定义域
        
        Returns:
            选中的变量或None(如果都已赋值)
        """
        unassigned = [v for v in self.variables if v not in assignment]
        if not unassigned:
            return None
        
        if self.var_ordering == VarOrdering.STATIC:
            return unassigned[0]
        
        elif self.var_ordering == VarOrdering.MRV:
            # 选择定义域最小的
            return min(unassigned, key=lambda v: len(remaining_domains[v]))
        
        elif self.var_ordering == VarOrdering.DEGREE:
            # 选择邻居最多的
            return max(unassigned, key=lambda v: len(self.neighbors[v]))
        
        elif self.var_ordering == VarOrdering.MRV_DEGREE:
            # MRV + 度打破平局
            return min(unassigned, 
                     key=lambda v: (len(remaining_domains[v]), -len(self.neighbors[v])))
        
        return unassigned[0]
    
    def order_values(self, var: str, remaining_domains: Dict[str, Set[Any]],
                    assignment: Dict[str, Any]) -> List[Any]:
        """
        对变量的值进行排序
        
        Args:
            var: 变量
            remaining_domains: 剩余定义域
            assignment: 当前赋值
        
        Returns:
            排序后的值列表
        """
        values = sorted(remaining_domains[var])
        
        if self.val_ordering == ValOrdering.STATIC:
            return values
        
        elif self.val_ordering == ValOrdering.LCV:
            # 最少约束值:选择能最大限度保留邻居定义域的值
            def count_conflicts(value):
                count = 0
                for neighbor in self.neighbors[var]:
                    if neighbor in assignment:
                        continue
                    constraint = self.get_constraint(var, neighbor)
                    for neighbor_val in remaining_domains[neighbor]:
                        if not constraint(value, neighbor_val):
                            count += 1
                return count
            
            return sorted(values, key=count_conflicts)
        
        return values
    
    def forward_check(self, var: str, value: Any,
                     remaining_domains: Dict[str, Set[Any]]) -> Optional[Dict[str, Set[Any]]]:
        """
        前向检查:更新邻居的定义域
        
        Args:
            var: 被赋值的变量
            value: 赋予的值
            remaining_domains: 剩余定义域
        
        Returns:
            更新后的定义域或None(如果失败)
        """
        new_domains = {v: remaining_domains[v].copy() for v in self.variables}
        
        for neighbor in self.neighbors[var]:
            if neighbor in remaining_domains:
                constraint = self.get_constraint(var, neighbor)
                to_remove = set()
                
                for neighbor_val in new_domains[neighbor]:
                    if not constraint(value, neighbor_val):
                        to_remove.add(neighbor_val)
                
                for rem in to_remove:
                    new_domains[neighbor].discard(rem)
                
                if not new_domains[neighbor]:
                    return None
        
        return new_domains
    
    def ac3_reduce(self, domains: Dict[str, Set[Any]]) -> Optional[Dict[str, Set[Any]]]:
        """
        使用AC-3简化定义域
        
        Args:
            domains: 初始定义域
        
        Returns:
            简化后的定义域或None(如果某变量定义域为空)
        """
        from collections import deque
        
        new_domains = {v: domains[v].copy() for v in self.variables}
        queue = deque()
        
        for v1, v2, _ in self.constraints:
            queue.append((v1, v2))
            queue.append((v2, v1))
        
        while queue:
            var1, var2 = queue.popleft()
            
            removed = False
            to_remove = set()
            
            constraint = self.get_constraint(var1, var2)
            
            for val1 in new_domains[var1]:
                # 检查是否存在var2的值满足约束
                compatible = False
                for val2 in new_domains[var2]:
                    if constraint(val1, val2):
                        compatible = True
                        break
                
                if not compatible:
                    to_remove.add(val1)
                    removed = True
            
            for val in to_remove:
                new_domains[var1].discard(val)
            
            if removed and not new_domains[var1]:
                return None
            
            if removed:
                for neighbor in self.neighbors[var1]:
                    if neighbor != var2:
                        queue.append((neighbor, var1))
        
        return new_domains
    
    def backtrack(self, assignment: Dict[str, Any],
                 remaining_domains: Dict[str, Set[Any]]) -> Optional[Dict[str, Any]]:
        """
        回溯搜索
        
        Args:
            assignment: 当前赋值
            remaining_domains: 每个变量的剩余定义域
        
        Returns:
            完整赋值或None
        """
        self.nodes_explored += 1
        
        # 检查是否完成
        if len(assignment) == len(self.variables):
            return assignment
        
        # 更新最大深度
        self.max_depth = max(self.max_depth, len(assignment))
        
        # 选择变量
        var = self.select_variable(assignment, remaining_domains)
        if var is None:
            return assignment
        
        # 选择值
        for value in self.order_values(var, remaining_domains, assignment):
            # 检查一致性
            if not self.is_consistent(var, value, assignment):
                continue
            
            # 赋值
            assignment[var] = value
            
            # 推理
            new_domains = remaining_domains.copy()
            if self.forward_checking:
                new_domains[var] = {value}
                fd_result = self.forward_check(var, value, new_domains)
                if fd_result is None:
                    del assignment[var]
                    continue
                new_domains = fd_result
            
            # 递归
            result = self.backtrack(assignment, new_domains)
            if result is not None:
                return result
            
            # 回溯
            del assignment[var]
        
        return None
    
    def solve(self) -> Optional[Dict[str, Any]]:
        """
        求解CSP
        
        Returns:
            满足所有约束的赋值或None
        """
        self.nodes_explored = 0
        self.max_depth = 0
        
        # 初始定义域
        initial_domains = {v: self.domains[v].copy() for v in self.variables}
        
        # 如果启用弧一致性,先简化
        if self.arc_consistency:
            reduced = self.ac3_reduce(initial_domains)
            if reduced is None:
                return None
            initial_domains = reduced
        
        # 回溯搜索
        result = self.backtrack({}, initial_domains)
        
        print(f"  搜索统计: 节点数={self.nodes_explored}, 最大深度={self.max_depth}")
        
        return result
    
    def solve_all(self) -> List[Dict[str, Any]]:
        """
        找出所有解
        
        Returns:
            所有解的列表
        """
        solutions = []
        
        def backtrack_all(assignment: Dict[str, Any], remaining_domains: Dict[str, Set[Any]]):
            if len(assignment) == len(self.variables):
                solutions.append(assignment.copy())
                return
            
            var = self.select_variable(assignment, remaining_domains)
            
            for value in sorted(remaining_domains[var]):
                if self.is_consistent(var, value, assignment):
                    assignment[var] = value
                    new_domains = remaining_domains.copy()
                    
                    if self.forward_checking:
                        fd_result = self.forward_check(var, value, new_domains)
                        if fd_result is None:
                            del assignment[var]
                            continue
                        new_domains = fd_result
                    
                    backtrack_all(assignment, new_domains)
                    del assignment[var]
        
        initial_domains = {v: self.domains[v].copy() for v in self.variables}
        backtrack_all({}, initial_domains)
        
        return solutions


# 测试代码
if __name__ == "__main__":
    # 测试1: 地图着色
    print("测试1 - 地图着色(澳大利亚):")
    variables = ['WA', 'NT', 'SA', 'Q', 'NSW', 'V', 'T']
    colors = {1, 2, 3, 4}
    domains = {v: colors.copy() for v in variables}
    
    constraints = [
        ('WA', 'NT', lambda a, b: a != b),
        ('WA', 'SA', lambda a, b: a != b),
        ('NT', 'SA', lambda a, b: a != b),
        ('NT', 'Q', lambda a, b: a != b),
        ('SA', 'Q', lambda a, b: a != b),
        ('SA', 'NSW', lambda a, b: a != b),
        ('SA', 'V', lambda a, b: a != b),
        ('Q', 'NSW', lambda a, b: a != b),
        ('NSW', 'V', lambda a, b: a != b),
    ]
    
    solver = CSPSearchSolver(variables, domains, constraints)
    solver.var_ordering = VarOrdering.MRV_DEGREE
    solver.val_ordering = ValOrdering.LCV
    
    result = solver.solve()
    print(f"  解: {result}")
    
    # 测试2: 4皇后问题
    print("\n测试2 - 4皇后问题:")
    n = 4
    variables = [f'Q{i}' for i in range(n)]
    domains = {v: set(range(n)) for v in variables}
    
    constraints = []
    for i in range(n):
        for j in range(i + 1, n):
            offset = j - i
            constraints.append((f'Q{i}', f'Q{j}', 
                              lambda a, b, d=offset: a != b and abs(a - b) != d))
    
    solver2 = CSPSearchSolver(variables, domains, constraints)
    solver2.forward_checking = True
    solver2.arc_consistency = True
    
    result2 = solver2.solve()
    if result2:
        board = [['.' for _ in range(n)] for _ in range(n)]
        for var, col in result2.items():
            row = int(var[1])
            board[row][col] = 'Q'
        print("  解:")
        for row in board:
            print("  " + " ".join(row))
    
    # 测试3: 所有解
    print("\n测试3 - 4皇后所有解:")
    solutions = solver2.solve_all()
    print(f"  解的数量: {len(solutions)}")
    for i, sol in enumerate(solutions[:3], 1):
        print(f"  解{i}: {sol}")
    
    # 测试4: 不同策略比较
    print("\n测试4 - 策略比较(5皇后):")
    n = 5
    variables = [f'Q{i}' for i in range(n)]
    domains = {v: set(range(n)) for v in variables}
    
    constraints = []
    for i in range(n):
        for j in range(i + 1, n):
            offset = j - i
            constraints.append((f'Q{i}', f'Q{j}', 
                              lambda a, b, d=offset: a != b and abs(a - b) != d))
    
    for var_order in [VarOrdering.STATIC, VarOrdering.MRV, VarOrdering.MRV_DEGREE]:
        for fc in [False, True]:
            solver = CSPSearchSolver(variables, domains, constraints)
            solver.var_ordering = var_order
            solver.forward_checking = fc
            
            import time
            start = time.time()
            result = solver.solve()
            elapsed = time.time() - start
            
            print(f"  {var_order.name}, FC={fc}: 节点={solver.nodes_explored}, 时间={elapsed:.4f}s")
    
    print("\n所有测试完成!")
