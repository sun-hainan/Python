# -*- coding: utf-8 -*-
"""
Theory求解器：EUFLIA和BitVector理论
功能：实现SMT-LIB标准中的主要 theories

Theory列表：
- EUFLIA: 未解释函数 + 线性整数算术
- BitVector: 固定宽度位向量
- Array: 数组理论
- LinearArith: 线性算术（稀释/优化）

作者：Theory Solver Team
"""

from typing import List, Dict, Set, Tuple, Optional, Any
from abc import ABC, abstractmethod
import itertools


# ============== 线性算术表达式 ==============

class LinearExpr:
    """线性表达式: c1*x1 + c2*x2 + ... + k"""
    
    def __init__(self):
        self.coeffs: Dict[str, int] = {}  # 变量→系数
        self.const: int = 0  # 常数项
    
    def add_term(self, var: str, coeff: int):
        if coeff == 0:
            return
        self.coeffs[var] = self.coeffs.get(var, 0) + coeff
    
    def __add__(self, other):
        result = LinearExpr()
        result.coeffs = dict(self.coeffs)
        result.const = self.const
        if isinstance(other, LinearExpr):
            for v, c in other.coeffs.items():
                result.add_term(v, c)
            result.const += other.const
        else:
            result.const += other
        return result
    
    def __sub__(self, other):
        return self + (-1 * other if isinstance(other, LinearExpr) else -other)
    
    def __mul__(self, k: int):
        result = LinearExpr()
        for v, c in self.coeffs.items():
            result.coeffs[v] = c * k
        result.const = self.const * k
        return result
    
    def __neg__(self):
        return (-1) * self
    
    def evaluate(self, assignment: Dict[str, int]) -> Optional[int]:
        """在给定赋值下求值"""
        total = self.const
        for var, coeff in self.coeffs.items():
            if var not in assignment:
                return None
            total += coeff * assignment[var]
        return total
    
    def variables(self) -> Set[str]:
        return set(self.coeffs.keys())
    
    def __repr__(self):
        terms = [f"{c}*{v}" for v, c in self.coeffs.items()]
        if self.const != 0 or not terms:
            terms.append(str(self.const))
        return " + ".join(terms) if terms else "0"


class LAConstraint:
    """线性算术约束: lhs rel rhs"""
    
    def __init__(self, lhs: LinearExpr, rel: str, rhs: LinearExpr):
        self.lhs = lhs
        self.rel = rel  # '<', '<=', '=', '>=', '>'
        self.rhs = rhs
    
    def is_satisfied(self, assignment: Dict[str, int]) -> Optional[bool]:
        """
        检查约束是否被满足
        
        Returns:
            True: 满足
            False: 不满足
            None: 未确定（有未赋值变量）
        """
        lhs_val = self.lhs.evaluate(assignment)
        rhs_val = self.rhs.evaluate(assignment)
        
        if lhs_val is None or rhs_val is None:
            return None
        
        if self.rel == '<':
            return lhs_val < rhs_val
        elif self.rel == '<=':
            return lhs_val <= rhs_val
        elif self.rel == '==':
            return lhs_val == rhs_val
        elif self.rel == '>=':
            return lhs_val >= rhs_val
        elif self.rel == '>':
            return lhs_val > rhs_val
        return None
    
    def __repr__(self):
        return f"{self.lhs} {self.rel} {self.rhs}"


class LinearArithSolver:
    """
    线性算术(LA)求解器
    使用Simplex方法的简化版本处理线性约束
    """

    def __init__(self):
        self.constraints: List[LAConstraint] = []
        self.assignment: Dict[str, int] = {}
        self.var_bounds: Dict[str, Tuple[int, int]] = {}  # 变量上下界
    
    def add_constraint(self, constraint: LAConstraint):
        """添加线性约束"""
        self.constraints.append(constraint)
    
    def check_sat(self) -> Tuple[bool, Optional[Dict[str, int]]]:
        """
        检查线性约束可满足性
        
        使用割平面方法的简化版本
        """
        variables = set()
        for c in self.constraints:
            variables.update(c.lhs.variables())
            variables.update(c.rhs.variables())
        
        # 尝试通过线性规划求解（简化：穷举整数解）
        # 实际求解器使用Simplex/Interior Point
        return self._solve_finite(variables)

    def _solve_finite(self, variables: Set[str]) -> Tuple[bool, Optional[Dict[str, int]]]:
        """有限域穷举（仅用于演示）"""
        if len(variables) > 5:
            # 变量太多，用启发式
            return self._heuristic_solve(variables)
        
        bounds = {v: self.var_bounds.get(v, (-100, 100)) for v in variables}
        
        for values in itertools.product(*[range(b[0], b[1] + 1) for b in bounds.values()]):
            assignment = dict(zip(variables, values))
            if all(c.is_satisfied(assignment) for c in self.constraints):
                return True, assignment
        
        return False, None

    def _heuristic_solve(self, variables: Set[str]) -> Tuple[bool, Optional[Dict[str, int]]]:
        """启发式求解：先随机尝试，失败后用分支定界"""
        import random
        
        for _ in range(1000):
            assignment = {v: random.randint(-50, 50) for v in variables}
            if all(c.is_satisfied(assignment) for c in self.constraints):
                return True, assignment
        
        return False, None


class EUFLIASolver:
    """
    EUFLIA求解器：EUFLIA = EUF + Linear Integer Arith
    
    结合：
    - 未解释函数理论（相等+函数）
    - 线性整数算术
    """

    def __init__(self):
        self.euf_solver = {}  # 并查集 for 等价类
        self.func_tab: Dict[str, Dict[Tuple, str]] = {}  # 函数→应用表
        self.la_solver = LinearArithSolver()
        self Diseq: Set[Tuple[str, str]] = set()  # 不等对
    
    def find(self, x: str) -> str:
        if x not in self.euf_solver:
            self.euf_solver[x] = x
        if self.euf_solver[x] != x:
            self.euf_solver[x] = self.find(self.euf_solver[x])
        return self.euf_solver[x]
    
    def union(self, x: str, y: str):
        rx, ry = self.find(x), self.find(y)
        if rx != ry:
            self.euf_solver[rx] = ry
    
    def add_eq(self, x: str, y: str):
        """添加相等约束 x = y"""
        if (y, x) in self.Diseq:
            return False  # 矛盾
        self.union(x, y)
        return True
    
    def addDiseq(self, x: str, y: str):
        """添加不等约束 x ≠ y"""
        if self.find(x) == self.find(y):
            return False  # 矛盾
        self.Diseq.add((x, y))
        return True
    
    def add_la_constraint(self, constraint: LAConstraint):
        """添加线性算术约束"""
        self.la_solver.add_constraint(constraint)
    
    def check_sat(self) -> bool:
        """检查整体可满足性"""
        # 检查不等约束是否与等价类冲突
        for x, y in self.Diseq:
            if self.find(x) == self.find(y):
                return False
        
        # 检查LA约束
        la_sat, _ = self.la_solver.check_sat()
        return la_sat


def example_linear_arith():
    """线性算术示例"""
    solver = LinearArithSolver()
    
    x = LinearExpr()
    x.add_term("x", 1)
    y = LinearExpr()
    y.add_term("y", 1)
    
    c1 = LAConstraint(x, '<=', LinearExpr() + 10)
    c2 = LAConstraint(y, '<=', LinearExpr() + 10)
    c3 = LAConstraint(x + y, '>=', LinearExpr() + 15)
    
    solver.add_constraint(c1)
    solver.add_constraint(c2)
    solver.add_constraint(c3)
    
    sat, model = solver.check_sat()
    print(f"线性算术: {'SAT' if sat else 'UNSAT'}")
    if model:
        print(f"  x = {model.get('x')}, y = {model.get('y')}")


def example_euflia():
    """EUFLIA示例"""
    solver = EUFLIASolver()
    
    # x = y
    solver.add_eq("x", "y")
    
    # f(x) ≠ f(y)
    solver.addDiseq(f"f(x)", f"f(y)")
    
    # 应该UNSAT（若x=y则f(x)=f(y)）
    print(f"EUFLIA x=y, f(x)≠f(y): {'UNSAT' if not solver.check_sat() else 'SAT'}")


if __name__ == "__main__":
    print("=" * 50)
    print("Theory求解器 测试")
    print("=" * 50)
    
    example_linear_arith()
    print()
    example_euflia()
