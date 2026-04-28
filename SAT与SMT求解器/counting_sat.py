# -*- coding: utf-8 -*-
"""
#SAT计数问题求解器
功能：计算SAT实例的解的数量

#SAT问题：
- 输入：CNF公式F
- 输出：满足F的变量赋值数量

方法：
1. DPLL + 计数：递归分裂，合并相同分支结果
2. 知识编译：将公式编译为神经网络/DD等结构
3. 重要性采样：蒙特卡洛估计

作者：Counting SAT Team
"""

from typing import List, Dict, Tuple, Optional
from functools import lru_cache


class CountingDPLL:
    """
    DPLL + 计数算法
    
    核心思想：
    - 对每个决策分支，记录满足该分支的解的数量
    - 单元传播后直接求值
    - 合并结果时加法
    """

    def __init__(self, cnf: List[List[int]]):
        self.cnf = cnf
        self.n_vars = self._count_vars()
        self.count_cache: Dict[Tuple, int] = {}

    def _count_vars(self) -> int:
        max_var = 0
        for clause in self.cnf:
            for lit in clause:
                max_var = max(max_var, abs(lit))
        return max_var

    def count(self) -> int:
        """
        计算满足赋值数量
        
        Returns:
            解的数量（可能很大）
        """
        return self._count_rec(self.cnf, {})

    def _count_rec(self, cnf: List[List[int]], 
                   assignment: Dict[int, bool]) -> int:
        """
        递归计数
        
        Args:
            cnf: 当前CNF
            assignment: 当前赋值
            
        Returns:
            解的数量
        """
        # 应用当前赋值到CNF
        new_cnf = self._apply_assignment(cnf, assignment)
        
        # 检查空子句
        for clause in new_cnf:
            if not clause:
                return 0
        
        # 检查是否所有子句已满足
        if not new_cnf:
            return 2 ** (self.n_vars - len(assignment))
        
        # 单元传播
        new_cnf, unit = self._unit_propagate(new_cnf, assignment)
        if unit is not None:
            new_assignment = assignment.copy()
            new_assignment[unit[0]] = unit[1]
            return self._count_rec(new_cnf, new_assignment)
        
        # 选择决策变量
        var = self._select_variable(new_cnf, assignment)
        if var is None:
            return 1
        
        # 分支：尝试True
        assign_true = assignment.copy()
        assign_true[var] = True
        count_true = self._count_rec(new_cnf, assign_true)
        
        # 分支：尝试False
        assign_false = assignment.copy()
        assign_false[var] = False
        count_false = self._count_rec(new_cnf, assign_false)
        
        return count_true + count_false

    def _apply_assignment(self, cnf: List[List[int]], 
                          assignment: Dict[int, bool]) -> List[List[int]]:
        """将赋值应用到CNF"""
        result = []
        for clause in cnf:
            new_clause = []
            satisfied = False
            for lit in clause:
                var = abs(lit)
                if var in assignment:
                    if (assignment[var] and lit > 0) or (not assignment[var] and lit < 0):
                        satisfied = True
                        break
                else:
                    new_clause.append(lit)
            if not satisfied:
                if not new_clause:
                    return [[]]  # 空子句
                result.append(new_clause)
        return result

    def _unit_propagate(self, cnf: List[List[int]], 
                         assignment: Dict[int, bool]) -> Tuple[List[List[int]], Optional[Tuple[int, bool]]]:
        """单元传播，返回(简化CNF, 单元文字或None)"""
        while True:
            unit_lit = None
            for clause in cnf:
                unassigned = [lit for lit in clause if abs(lit) not in assignment]
                if len(unassigned) == 1:
                    unit_lit = unassigned[0]
                    break
            
            if unit_lit is None:
                break
            
            var = abs(unit_lit)
            val = unit_lit > 0
            
            # 避免循环赋值
            if var in assignment and assignment[var] != val:
                return [[]], None  # 冲突
            
            assignment[var] = val
            
            # 应用新赋值
            new_cnf = []
            for clause in cnf:
                new_clause = []
                satisfied = False
                for lit in clause:
                    v = abs(lit)
                    if v == var:
                        if (assignment[var] and lit > 0) or (not assignment[var] and lit < 0):
                            satisfied = True
                            break
                    elif v in assignment:
                        if (assignment[v] and lit > 0) or (not assignment[v] and lit < 0):
                            satisfied = True
                            break
                    else:
                        new_clause.append(lit)
                if not satisfied:
                    if not new_clause:
                        return [[]], None
                    new_cnf.append(new_clause)
            cnf = new_cnf
        
        return cnf, unit_lit

    def _select_variable(self, cnf: List[List[int]], 
                         assignment: Dict[int, bool]) -> Optional[int]:
        """选择未赋值变量"""
        for clause in cnf:
            for lit in clause:
                var = abs(lit)
                if var not in assignment:
                    return var
        return None


class ApproxCounting:
    """
    近似计数（蒙特卡洛方法）
    
    使用重要性采样估计解的数量
    适用于解数量极大或公式极复杂的情况
    """

    def __init__(self, cnf: List[List[int]], n_vars: int):
        self.cnf = cnf
        self.n_vars = n_vars

    def _is_satisfied(self, assignment: Dict[int, bool]) -> bool:
        """检查赋值是否满足公式"""
        for clause in self.cnf:
            clause_sat = False
            for lit in clause:
                var = abs(lit)
                val = assignment[var]
                if (lit > 0 and val) or (lit < 0 and not val):
                    clause_sat = True
                    break
            if not clause_sat:
                return False
        return True

    def _random_assignment(self) -> Dict[int, bool]:
        """生成随机赋值"""
        import random
        return {i: random.choice([True, False]) for i in range(1, self.n_vars + 1)}

    def estimate(self, n_samples: int = 10000) -> Tuple[int, float]:
        """
        估计解的数量
        
        Returns:
            (估计值, 相对误差估计)
        """
        import random
        random.seed()
        
        satisfied_count = 0
        total_samples = n_samples
        
        for _ in range(total_samples):
            assignment = self._random_assignment()
            if self._is_satisfied(assignment):
                satisfied_count += 1
        
        # 估计：满足比例 × 总可能赋值数
        ratio = satisfied_count / total_samples
        total_assignments = 2 ** self.n_vars
        estimate = int(ratio * total_assignments)
        
        # 简单误差估计
        if satisfied_count == 0:
            error = 1.0
        else:
            error = 1.0 / (satisfied_count ** 0.5)
        
        return estimate, error


def example_counting():
    """计数SAT示例"""
    cnf = [
        [1, 2],
        [-1, 3],
        [-2, 3]
    ]
    
    solver = CountingDPLL(cnf)
    count = solver.count()
    print(f"CNF {cnf}")
    print(f"解的数量: {count}")
    print(f"理论上限: {2 ** solver.n_vars}")

    # 验证
    from dpll_solver import DPLLSolver
    dpll = DPLLSolver(cnf)
    result = dpll.solve()
    print(f"实际SAT: {'是' if result else '否'}")

    # 已知：(x1 ∨ x2) ∧ (¬x1 ∨ x3) ∧ (¬x2 ∨ x3) 有4个解
    cnf2 = [
        [1, 2],
        [-1, 3],
        [-2, 3]
    ]
    solver2 = CountingDPLL(cnf2)
    print(f"\n第二个CNF解数量: {solver2.count()}")


def example_unsat_counting():
    """UNSAT计数（应为0）"""
    cnf = [
        [1],
        [-1]
    ]  # x1 ∧ ¬x1
    
    solver = CountingDPLL(cnf)
    count = solver.count()
    print(f"矛盾公式解数量: {count}")


def example_approx():
    """近似计数示例"""
    import random
    random.seed(42)
    
    # 随机生成一个SAT概率较高的公式
    n_vars = 10
    n_clauses = 30
    cnf = []
    for _ in range(n_clauses):
        clause = [random.choice([-1, 1]) * random.randint(1, n_vars) 
                  for _ in range(3)]
        cnf.append(clause)
    
    approx = ApproxCounting(cnf, n_vars)
    est, err = approx.estimate(5000)
    
    print(f"近似计数: {est} ± {int(err * est)}")
    print(f"理论上限: {2 ** n_vars}")


if __name__ == "__main__":
    print("=" * 50)
    print("#SAT计数求解器 测试")
    print("=" * 50)
    
    example_counting()
    print()
    example_unsat_counting()
    print()
    example_approx()
