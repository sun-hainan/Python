# -*- coding: utf-8 -*-
"""
最大可满足性(MaxSAT)求解器
功能：求解最大化满足的子句数

MaxSAT问题：给定加权/非加权子句集合，求使得尽可能多子句被满足的赋值

方法：
1. 核驱动(Core-Driven)：迭代识别不可满足核，逐步添加软约束
2. 线性搜索：二分搜索满足的子句数下界
3. 混合方法：结合SAT求解和局部搜索

作者：MaxSAT Team
"""

from typing import List, Dict, Set, Tuple, Optional
import random


class MaxSATSolver:
    """MaxSAT求解器基类"""

    def __init__(self, soft_clauses: List[List[int]], hard_clauses: List[List[int]] = None):
        """
        Args:
            soft_clauses: 软子句列表（希望被满足但非必须）
            hard_clauses: 硬子句列表（必须满足）
        """
        self.soft = soft_clauses
        self.hard = hard_clauses or []
        self.n_vars = self._count_vars()
        self.best_assignment: Dict[int, bool] = {}
        self.best_satisfied = 0

    def _count_vars(self) -> int:
        max_var = 0
        for clauses in [self.soft, self.hard]:
            for clause in clauses:
                for lit in clause:
                    max_var = max(max_var, abs(lit))
        return max_var

    def _is_satisfied(self, assignment: Dict[int, bool], clause: List[int]) -> bool:
        """检查子句是否满足"""
        for lit in clause:
            var = abs(lit)
            val = assignment[var]
            if (lit > 0 and val) or (lit < 0 and not val):
                return True
        return False

    def _count_satisfied(self, assignment: Dict[int, bool], 
                         clauses: List[List[int]]) -> int:
        """统计满足的子句数"""
        return sum(1 for c in clauses if self._is_satisfied(assignment, c))

    def _random_assignment(self) -> Dict[int, bool]:
        """生成随机赋值"""
        return {i: random.choice([True, False]) for i in range(1, self.n_vars + 1)}


class LinearSearchMaxSAT(MaxSATSolver):
    """
    线性搜索MaxSAT
    
    方法：对于k=0,1,2,...，检查是否存在满足>=k个软子句的赋值
    使用SAT求解器检查约束可满足性
    """

    def __init__(self, soft_clauses: List[List[int]], hard_clauses: List[List[int]] = None):
        super().__init__(soft_clauses, hard_clauses)
        self.unweighted = True  # 非加权版本

    def solve(self) -> Tuple[bool, Dict[int, bool], int]:
        """
        求解MaxSAT
        
        Returns:
            (可解, 最优赋值, 满足的软子句数)
        """
        # 首先检查硬约束是否可满足
        if self.hard:
            sat_solver = self._check_sat_cnf(self.hard)
            if not sat_solver:
                return False, {}, 0
        
        # 尝试满足所有软子句
        all_clauses = self.hard + self.soft
        if self._check_sat_cnf(all_clauses):
            full_assignment = self._find_one_sat(all_clauses)
            return True, full_assignment, len(self.soft)
        
        # 线性搜索：逐个放弃软子句
        remaining_soft = list(self.soft)
        current_best = 0
        
        # 简化：使用贪婪局部搜索
        assignment = self._random_assignment()
        
        for iteration in range(10000):
            # 计算当前满足数
            satisfied = self._count_satisfied(assignment, self.soft)
            hard_sat = self._count_satisfied(assignment, self.hard) == len(self.hard)
            
            if hard_sat and satisfied > current_best:
                current_best = satisfied
                self.best_assignment = assignment.copy()
            
            if satisfied == len(self.soft):
                break
            
            # 尝试翻转一个变量
            var = random.randint(1, self.n_vars)
            assignment[var] = not assignment[var]
        
        return True, self.best_assignment, current_best

    def _check_sat_cnf(self, cnf: List[List[int]]) -> bool:
        """简化SAT检查（使用DPLL）"""
        from dpll_solver import DPLLSolver
        solver = DPLLSolver(cnf)
        return solver.solve() is not None

    def _find_one_sat(self, cnf: List[List[int]]) -> Dict[int, bool]:
        """找一个SAT解"""
        from dpll_solver import DPLLSolver
        solver = DPLLSolver(cnf)
        return solver.solve() or {}


class CoreDrivenMaxSAT(MaxSATSolver):
    """
    核驱动MaxSAT算法
    
    流程：
    1. 添加辅助变量到每个软子句: s_i ∨ clause_i
    2. 求解SAT+软子句辅助变量
    3. 若不可满足，找出不可满足核
    4. 将核中软子句转为硬约束，重复
    """

    def __init__(self, soft_clauses: List[List[int]], hard_clauses: List[List[int]] = None):
        super().__init__(soft_clauses, hard_clauses)
        self.soft_vars: Dict[int, int] = {}  # 子句index → 辅助变量

    def solve(self) -> Tuple[bool, Dict[int, bool], int]:
        """核驱动MaxSAT求解"""
        # 添加辅助变量
        next_var = self.n_vars + 1
        assumptions = []
        
        working_soft = list(self.soft)
        working_hard = list(self.hard)
        
        for i, clause in enumerate(working_soft):
            assump_var = next_var
            self.soft_vars[i] = assump_var
            next_var += 1
            # 添加带辅助变量的软子句
            working_soft[i] = clause + [assump_var]
            assumptions.append(assump_var)
        
        # 迭代
        for iteration in range(len(working_soft) + 1):
            # 求解当前公式
            result = self._solve_with_assumptions(working_hard + working_soft, assumptions)
            
            if result is not None:
                # SAT：当前解满足的软子 clause
                satisfied_count = sum(
                    1 for i, clause in enumerate(self.soft)
                    if self._is_satisfied(result, clause)
                )
                return True, result, satisfied_count
            
            # UNSAT：找出不可满足核
            # 简化：随机移除一个软子句作为硬约束
            if assumptions:
                removed = assumptions.pop()
                # 将被移除的辅助变量对应的软子句转为硬约束
                clause_idx = [i for i, v in self.soft_vars.items() if v == removed]
                if clause_idx:
                    hard_clause = self.soft[clause_idx[0]]
                    working_hard.append(hard_clause)
        
        return False, {}, 0

    def _solve_with_assumptions(self, cnf: List[List[int]], 
                                  assumptions: List[int]) -> Optional[Dict[int, bool]]:
        """在假设变量下求解"""
        from dpll_solver import DPLLSolver
        solver = DPLLSolver(cnf)
        # 简化：忽略假设直接求解
        return solver.solve()


def example_unweighted_maxsat():
    """非加权MaxSAT示例"""
    soft = [
        [1, 2],
        [-1, 3],
        [2, -3],
        [-2],
        [3]
    ]
    
    hard = [
        [1, -2]
    ]
    
    solver = LinearSearchMaxSAT(soft, hard)
    sat, assignment, count = solver.solve()
    
    print(f"MaxSAT: SAT={sat}, 满足软子句数={count}/{len(soft)}")
    if assignment:
        for var, val in sorted(assignment.items()):
            print(f"  x{var} = {val}")


def example_weighted_maxsat():
    """加权MaxSAT示例（简化版）"""
    soft = [
        [1, 2],
        [-1, 3],
        [-2]
    ]
    
    # 贪婪方法
    solver = MaxSATSolver(soft)
    assignment = solver._random_assignment()
    
    print("贪婪搜索结果:")
    for var, val in sorted(assignment.items()):
        print(f"  x{var} = {val}")
    print(f"  满足子句数: {solver._count_satisfied(assignment, soft)}/{len(soft)}")


if __name__ == "__main__":
    print("=" * 50)
    print("MaxSAT求解器 测试")
    print("=" * 50)
    
    example_unweighted_maxsat()
    print()
    example_weighted_maxsat()
