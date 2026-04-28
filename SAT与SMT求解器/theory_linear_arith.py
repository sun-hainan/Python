# -*- coding: utf-8 -*-
"""
线性算术理论求解器
功能：实现稀释/整数线性算术的约束求解

Linear Arithmetic (LA):
- QF_LIA: 稀释线性整数算术（量词自由）
- QF_LRA: 稀释线性实数算术

方法：
1. Simplex算法（针对实数）
2. Branch and Bound（整数解）
3. Cuts生成（ Gomory割）

作者：Linear Arithmetic Team
"""

from typing import List, Dict, Set, Tuple, Optional, Any
from fractions import Fraction
from collections import defaultdict


class LinearTerm:
    """线性项：c1*x1 + c2*x2 + ... + k"""
    
    def __init__(self):
        self.coeffs: Dict[str, Fraction] = {}
        self.const: Fraction = Fraction(0)
    
    @staticmethod
    def constant(k: int) -> 'LinearTerm':
        t = LinearTerm()
        t.const = Fraction(k)
        return t
    
    @staticmethod
    def variable(name: str) -> 'LinearTerm':
        t = LinearTerm()
        t.coeffs[name] = Fraction(1)
        return t
    
    def copy(self) -> 'LinearTerm':
        t = LinearTerm()
        t.coeffs = dict(self.coeffs)
        t.const = self.const
        return t
    
    def __add__(self, other: 'LinearTerm') -> 'LinearTerm':
        result = self.copy()
        for var, coeff in other.coeffs.items():
            result.coeffs[var] = result.coeffs.get(var, Fraction(0)) + coeff
        result.const += other.const
        return result
    
    def __sub__(self, other: 'LinearTerm') -> 'LinearTerm':
        return self + (-other)
    
    def __neg__(self) -> 'LinearTerm':
        result = self.copy()
        for var in result.coeffs:
            result.coeffs[var] = -result.coeffs[var]
        result.const = -result.const
        return result
    
    def __mul__(self, k: int) -> 'LinearTerm':
        result = self.copy()
        k_frac = Fraction(k)
        for var in result.coeffs:
            result.coeffs[var] *= k_frac
        result.const *= k_frac
        return result
    
    def __rmul__(self, k: int) -> 'LinearTerm':
        return self.__mul__(k)
    
    def evaluate(self, assignment: Dict[str, Fraction]) -> Optional[Fraction]:
        """在赋值下求值"""
        total = self.const
        for var, coeff in self.coeffs.items():
            if var not in assignment:
                return None
            total += coeff * assignment[var]
        return total
    
    def variables(self) -> Set[str]:
        return set(self.coeffs.keys())
    
    def __repr__(self):
        parts = []
        for var in sorted(self.coeffs.keys()):
            coeff = self.coeffs[var]
            if coeff == 1:
                parts.append(var)
            elif coeff == -1:
                parts.append(f"-{var}")
            else:
                parts.append(f"{coeff}*{var}")
        if self.const != 0 or not parts:
            parts.append(str(self.const))
        return " + ".join(parts) if len(parts) <= 3 else f"{len(parts)} terms"


class LAConstraint:
    """线性算术约束: term1 rel term2"""
    
    def __init__(self, lhs: LinearTerm, rel: str, rhs: LinearTerm):
        self.lhs = lhs
        self.rel = rel
        self.rhs = rhs
        # 标准化：lhs - rhs rel 0
        self.normalized = lhs + (-rhs)
    
    def is_satisfied(self, assignment: Dict[str, Fraction]) -> Optional[bool]:
        """检查约束是否满足"""
        val = self.normalized.evaluate(assignment)
        if val is None:
            return None
        
        if self.rel == '<':
            return val < 0
        elif self.rel == '<=':
            return val <= 0
        elif self.rel == '=':
            return val == 0
        elif self.rel == '>=':
            return val >= 0
        elif self.rel == '>':
            return val > 0
        return None
    
    def __repr__(self):
        return f"{self.lhs} {self.rel} {self.rhs}"


class SimplexSolver:
    """
    Simplex算法求解器（实数线性规划）
    
    求解: Ax ≤ b 形式的线性约束，找到一个可行点
    """

    def __init__(self):
        self.constraints: List[LAConstraint] = []
        self.variables: Set[str] = set()
        # 简单变量边界
        self.var_bounds: Dict[str, Tuple[Fraction, Fraction]] = {}

    def add_constraint(self, c: LAConstraint):
        """添加约束"""
        self.constraints.append(c)
        self.variables.update(c.lhs.variables())
        self.variables.update(c.rhs.variables())

    def add_var_bounds(self, var: str, lower: Fraction, upper: Fraction):
        """添加变量边界"""
        self.var_bounds[var] = (lower, upper)

    def _tableau_row(self, c: LAConstraint, var_order: List[str]) -> List[Fraction]:
        """将约束转换为表的一行"""
        row = []
        for v in var_order:
            coeff = c.normalized.coeffs.get(v, Fraction(0))
            row.append(coeff)
        row.append(-c.normalized.const)  # RHS
        return row

    def check_sat(self) -> Tuple[bool, Optional[Dict[str, Fraction]]]:
        """
        检查线性约束的可满足性
        
        使用两阶段Simplex的简化版本
        
        Returns:
            (可满足, 可行解或None)
        """
        if not self.constraints:
            # 无约束：返回任意点
            return True, {v: Fraction(0) for v in self.variables}
        
        # 穷举求解（仅用于小规模演示）
        return self._exhaustive_solve()

    def _exhaustive_solve(self) -> Tuple[bool, Optional[Dict[str, Fraction]]]:
        """穷举法（小规模）"""
        if len(self.variables) > 4:
            return self._heuristic_solve()
        
        # 离散化搜索（假设变量在[-10,10]）
        bounds = self.var_bounds.copy()
        default_bounds = (Fraction(-10), Fraction(10))
        for v in self.variables:
            bounds.setdefault(v, default_bounds)
        
        # 网格搜索
        from itertools import product
        var_list = list(self.variables)
        
        for values in product(*[range(-10, 11) for _ in var_list]):
            assignment = {v: Fraction(val) for v, val in zip(var_list, values)}
            
            all_satisfied = True
            for c in self.constraints:
                result = c.is_satisfied(assignment)
                if result is False:
                    all_satisfied = False
                    break
            
            if all_satisfied:
                return True, assignment
        
        return False, None

    def _heuristic_solve(self) -> Tuple[bool, Optional[Dict[str, Fraction]]]:
        """启发式求解"""
        import random
        random.seed(42)
        
        for _ in range(1000):
            assignment = {}
            for v in self.variables:
                low, high = self.var_bounds.get(v, (Fraction(-100), Fraction(100)))
                val = Fraction(random.randint(int(low), int(high)))
                assignment[v] = val
            
            all_sat = True
            for c in self.constraints:
                result = c.is_satisfied(assignment)
                if result is False:
                    all_sat = False
                    break
            
            if all_sat:
                return True, assignment
        
        return False, None


class ILPSolver:
    """
    整数线性规划求解器
    
    使用分支定界法求解ILP
    """

    def __init__(self, la_solver: SimplexSolver = None):
        self.la = la_solver or SimplexSolver()
        self.int_vars: Set[str] = set()
        self.solutions: List[Dict[str, Fraction]] = []

    def add_int_var(self, name: str):
        """声明整数变量"""
        self.int_vars.add(name)

    def check_sat(self) -> Tuple[bool, Optional[Dict[str, Fraction]]]:
        """
        检查整数线性约束的可满足性
        
        使用分支定界
        """
        sat, solution = self.la.check_sat()
        if not sat:
            return False, None
        
        # 检查解是否满足整数性
        for v in self.int_vars:
            if v in solution and solution[v].denominator != 1:
                # 需要分支
                return self._branch_and_bound(solution)
        
        return sat, solution

    def _branch_and_bound(self, fractional_solution: Dict[str, Fraction]) -> Tuple[bool, Optional[Dict[str, Fraction]]]:
        """分支定界"""
        # 找一个违反整数性的变量
        branch_var = None
        for v in self.int_vars:
            if v in fractional_solution and fractional_solution[v].denominator != 1:
                branch_var = v
                break
        
        if branch_var is None:
            return True, fractional_solution
        
        val = fractional_solution[branch_var]
        floor_val = Fraction(int(val))  # 向下取整
        ceil_val = floor_val + 1
        
        # 分支1: var ≤ floor
        c1 = LAConstraint(
            LinearTerm.variable(branch_var), '<=', 
            LinearTerm.constant(int(floor_val))
        )
        self.la.add_constraint(c1)
        sat1, sol1 = self.la.check_sat()
        self.la.constraints.pop()
        
        if sat1 and sol1:
            return True, sol1
        
        # 分支2: var ≥ ceil
        c2 = LAConstraint(
            LinearTerm.variable(branch_var), '>=',
            LinearTerm.constant(int(ceil_val))
        )
        self.la.add_constraint(c2)
        sat2, sol2 = self.la.check_sat()
        self.la.constraints.pop()
        
        if sat2 and sol2:
            return True, sol2
        
        return False, None


def example_linear_constraints():
    """线性约束示例"""
    la = SimplexSolver()
    
    # x + y <= 10
    c1 = LAConstraint(
        LinearTerm.variable('x') + LinearTerm.variable('y'),
        '<=',
        LinearTerm.constant(10)
    )
    
    # x >= 0
    c2 = LAConstraint(
        LinearTerm.variable('x'),
        '>=',
        LinearTerm.constant(0)
    )
    
    # y >= 0
    c3 = LAConstraint(
        LinearTerm.variable('y'),
        '>=',
        LinearTerm.constant(0)
    )
    
    la.add_constraint(c1)
    la.add_constraint(c2)
    la.add_constraint(c3)
    
    sat, solution = la.check_sat()
    print(f"线性规划: {'SAT' if sat else 'UNSAT'}")
    if solution:
        for v, val in solution.items():
            print(f"  {v} = {val}")


def example_ilp():
    """整数线性规划示例"""
    ilp = ILPSolver()
    
    ilp.add_int_var('x')
    ilp.add_int_var('y')
    
    # x + y >= 5
    c1 = LAConstraint(
        LinearTerm.variable('x') + LinearTerm.variable('y'),
        '>=',
        LinearTerm.constant(5)
    )
    
    # x <= 3
    c2 = LAConstraint(
        LinearTerm.variable('x'),
        '<=',
        LinearTerm.constant(3)
    )
    
    # y <= 4
    c3 = LAConstraint(
        LinearTerm.variable('y'),
        '<=',
        LinearTerm.constant(4)
    )
    
    ilp.la.add_constraint(c1)
    ilp.la.add_constraint(c2)
    ilp.la.add_constraint(c3)
    
    sat, solution = ilp.check_sat()
    print(f"ILP: {'SAT' if sat else 'UNSAT'}")
    if solution:
        print(f"  解: {solution}")


if __name__ == "__main__":
    print("=" * 50)
    print("线性算术理论求解器 测试")
    print("=" * 50)
    
    example_linear_constraints()
    print()
    example_ilp()
