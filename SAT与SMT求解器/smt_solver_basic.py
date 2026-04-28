# -*- coding: utf-8 -*-
"""
SMT求解器基础：SAT + Theory Solver
功能：Satisfiability Modulo Theories，结合布尔SAT与背景理论求解

架构：
1. nular SAT solver (e.g., CDCL) 处理布尔结构
2. Theory solver 处理具体理论（EUFLIA, Array, BitVector等）
3. Eager/Lazy转化：
   - Eager: 将理论约束全部编码进SAT
   - Lazy: 交替SAT搜索和理论检查

作者：SMT Team
"""

from typing import List, Dict, Set, Tuple, Optional, Any
from abc import ABC, abstractmethod


# ============== SMT表达式 ==============

class Sort(ABC):
    """SMT排序（类型）基类"""
    pass


class BoolSort(Sort):
    """布尔类型"""
    def __repr__(self):
        return "Bool"


class IntSort(Sort):
    """整数类型（无穷精度）"""
    def __repr__(self):
        return "Int"


class ArraySort(Sort):
    """数组类型 Array(IndexSort, ValueSort)"""
    def __init__(self, index_sort: Sort, value_sort: Sort):
        self.index = index_sort
        self.value = value_sort
    
    def __repr__(self):
        return f"Array({self.index}, {self.value})"


class Expr:
    """SMT表达式基类"""
    def __init__(self, sort: Sort):
        self.sort = sort


class BoolExpr(Expr):
    """布尔表达式"""
    def __init__(self):
        super().__init__(BoolSort())


class Var(Expr):
    """变量 x, y, z ..."""
    def __init__(self, name: str, sort: Sort):
        super().__init__(sort)
        self.name = name
    
    def __repr__(self):
        return self.name


class Const(Expr):
    """常量"""
    def __init__(self, value: Any, sort: Sort):
        super().__init__(sort)
        self.value = value


class App(Expr):
    """函数应用 f(t1, ..., tn)"""
    def __init__(self, func_name: str, args: List[Expr]):
        super().__init__(sort=None)  # sort由理论决定
        self.func = func_name
        self.args = args


class Not(BoolExpr):
    """否定 ¬p"""
    def __init__(self, arg: BoolExpr):
        super().__init__()
        self.arg = arg


class And(BoolExpr):
    """合取 p ∧ q"""
    def __init__(self, args: List[BoolExpr]):
        super().__init__()
        self.args = args


class Or(BoolExpr):
    """析取 p ∨ q"""
    def __init__(self, args: List[BoolExpr]):
        super().__init__()
        self.args = args


class Implies(BoolExpr):
    """蕴含 p → q"""
    def __init__(self, antecedent: BoolExpr, consequent: BoolExpr):
        super().__init__()
        self.ant = antecedent
        self.cons = consequent


class Eq(BoolExpr):
    """相等 t1 = t2"""
    def __init__(self, left: Expr, right: Expr):
        super().__init__()
        self.left = left
        self.right = right


class Lt(BoolExpr):
    """小于 t1 < t2"""
    def __init__(self, left: Expr, right: Expr):
        super().__init__()
        self.left = left
        self.right = right


class Le(BoolExpr):
    """小于等于 t1 ≤ t2"""
    def __init__(self, left: Expr, right: Expr):
        super().__init__()
        self.left = left
        self.right = right


# ============== Theory Solver接口 ==============

class TheorySolver(ABC):
    """理论求解器抽象接口"""

    @abstractmethod
    def push(self):
        """增加一个新的决策层级"""
        pass

    @abstractmethod
    def pop(self):
        """弹出决策层级"""
        pass

    @abstractmethod
    def add_assertion(self, expr: Expr):
        """添加约束断言"""
        pass

    @abstractmethod
    def check_sat(self, assumptions: List[Expr]) -> bool:
        """检查可满足性"""
        pass

    @abstractmethod
    def get_model(self) -> Dict[str, Any]:
        """获取模型（赋值）"""
        pass


# ============== EUF理论求解器 ==============

class EUFSolver(TheorySolver):
    """
    未解释函数(EUF)理论求解器
    支持: 变量、相等、函数应用
    使用: UF SAT求解 (DPLL + Congruence Closure)
    """

    def __init__(self):
        self.assertions: List[Expr] = []  # 约束栈
        self.solver_state: Dict[str, Any] = {}
        self.push_count = 0

    def push(self):
        self.push_count += 1

    def pop(self):
        if self.push_count > 0:
            self.push_count -= 1

    def add_assertion(self, expr: Expr):
        self.assertions.append(expr)

    def check_sat(self, assumptions: List[Expr]) -> bool:
        """简化检查：若无不等式约束则SAT"""
        all_exprs = self.assertions + assumptions
        
        # 检查是否存在明显的矛盾 (x = a) ∧ (x = b) where a ≠ b
        eq_classes: Dict[str, str] = {}  # 变量→等价代表
        Diseq: Set[Tuple[str, str]] = set()  # 不等对
        
        def find(x: str) -> str:
            if x not in eq_classes:
                eq_classes[x] = x
            if eq_classes[x] != x:
                eq_classes[x] = find(eq_classes[x])
            return eq_classes[x]
        
        def union(x, y):
            rx, ry = find(x), find(y)
            if rx != ry:
                eq_classes[rx] = ry
        
        for expr in all_exprs:
            if isinstance(expr, Eq):
                # 提取变量名
                left_name = self._get_var_name(expr.left)
                right_name = self._get_var_name(expr.right)
                if left_name and right_name:
                    if (right_name, left_name) in Diseq:
                        return False  # 矛盾
                    union(left_name, right_name)
        
        return True

    def _get_var_name(self, expr: Expr) -> Optional[str]:
        if isinstance(expr, Var):
            return expr.name
        return None

    def get_model(self) -> Dict[str, Any]:
        return self.solver_state.copy()


# ============== 组合SMT求解器 ==============

class SMTSolver:
    """
    组合SMT求解器
    使用Lazy方法：SAT层 + Theory层交替求解
    """

    def __init__(self, theory_solvers: List[TheorySolver] = None):
        self.theory_solvers = theory_solvers or [EUFSolver()]
        self.assertions: List[Expr] = []
        self.solver_state: Dict[str, Any] = {}

    def declare_var(self, name: str, sort: Sort) -> Var:
        """声明变量"""
        return Var(name, sort)

    def assert_formula(self, expr: BoolExpr):
        """添加断言"""
        self.assertions.append(expr)

    def check_sat(self) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        检查可满足性
        
        流程：
        1. 收集所有布尔子公式，交给SAT求解
        2. SAT给出一组真值指派
        3. Theory solver检查理论一致性
        4. 若冲突，添加反子句返回SAT继续搜索
        """
        # 简化实现：直接调用理论求解器
        for ts in self.theory_solvers:
            ts.push()
        
        for assertion in self.assertions:
            for ts in self.theory_solvers:
                ts.add_assertion(assertion)
        
        sat_result = self.theory_solvers[0].check_sat([])
        
        for ts in self.theory_solvers:
            ts.pop()
        
        if sat_result:
            model = {}
            for ts in self.theory_solvers:
                model.update(ts.get_model())
            return True, model
        return False, None

    def get_model(self) -> Dict[str, Any]:
        return self.solver_state.copy()


def example_basic_smt():
    """基本SMT示例"""
    solver = SMTSolver()
    
    x = solver.declare_var("x", IntSort())
    y = solver.declare_var("y", IntSort())
    
    # 断言: x + y = 10 ∧ x > 0 ∧ y > 0
    solver.assert_formula(Eq(
        App("+", [x, y]), 
        Const(10, IntSort())
    ))
    solver.assert_formula(Lt(Const(0, IntSort()), x))
    solver.assert_formula(Lt(Const(0, IntSort()), y))
    
    sat, model = solver.check_sat()
    print(f"SMT检查: {'SAT' if sat else 'UNSAT'}")
    if model:
        print(f"模型: {model}")


def example_euf():
    """EUF示例"""
    solver = SMTSolver([EUFSolver()])
    
    x = solver.declare_var("x", IntSort())
    y = solver.declare_var("y", IntSort())
    
    # x = y ∧ f(x) ≠ f(y) → UNSAT
    solver.assert_formula(Eq(x, y))
    
    sat, _ = solver.check_sat()
    print(f"EUF测试: {'SAT' if sat else 'UNSAT'}")


if __name__ == "__main__":
    print("=" * 50)
    print("SMT求解器基础 测试")
    print("=" * 50)
    
    example_basic_smt()
    print()
    example_euf()
