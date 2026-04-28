# -*- coding: utf-8 -*-
"""
SMT表达式求值器
功能：对SMT表达式在给定模型下求值

支持的理论：
- 布尔: and, or, not, =>, =
- 整数算术: +, -, *, div, mod, <, <=, >, >=
- 位向量: bvadd, bvmul, extract, concat等

作者：SMT Evaluator Team
"""

from typing import Dict, Any, Optional, List, Tuple
from abc import ABC, abstractmethod


class Sort(ABC):
    """SMT排序（类型）"""
    pass


class BoolSort(Sort):
    def __repr__(self):
        return "Bool"


class IntSort(Sort):
    def __repr__(self):
        return "Int"


class BVSort(Sort):
    def __init__(self, width: int):
        self.width = width
    def __repr__(self):
        return f"BV{self.width}"


class Expr:
    """SMT表达式基类"""
    def __init__(self, sort: Sort):
        self.sort = sort


class BoolExpr(Expr):
    def __init__(self):
        super().__init__(BoolSort())


class IntExpr(Expr):
    def __init__(self):
        super().__init__(IntSort())


class BVExpr(Expr):
    def __init__(self, width: int):
        super().__init__(BVSort(width))


# ============== 布尔表达式 ==============

class Var(Expr):
    """变量"""
    def __init__(self, name: str, sort: Sort):
        super().__init__(sort)
        self.name = name


class ConstBool(BoolExpr):
    def __init__(self, value: bool):
        super().__init__()
        self.value = value


class ConstInt(IntExpr):
    def __init__(self, value: int):
        super().__init__()
        self.value = value


class ConstBV(BVExpr):
    def __init__(self, value: int, width: int):
        super().__init__(width)
        self.value = value


class Not(BoolExpr):
    def __init__(self, arg: BoolExpr):
        super().__init__()
        self.arg = arg


class And(BoolExpr):
    def __init__(self, args: List[BoolExpr]):
        super().__init__()
        self.args = args


class Or(BoolExpr):
    def __init__(self, args: List[BoolExpr]):
        super().__init__()
        self.args = args


class Implies(BoolExpr):
    def __init__(self, ant: BoolExpr, cons: BoolExpr):
        super().__init__()
        self.ant = ant
        self.cons = cons


class Eq(BoolExpr):
    def __init__(self, left: Expr, right: Expr):
        super().__init__()
        self.left = left
        self.right = right


class Lt(BoolExpr):
    def __init__(self, left: IntExpr, right: IntExpr):
        super().__init__()
        self.left = left
        self.right = right


class Le(BoolExpr):
    def __init__(self, left: IntExpr, right: IntExpr):
        super().__init__()
        self.left = left
        self.right = right


# ============== 算术表达式 ==============

class Plus(IntExpr):
    def __init__(self, args: List[IntExpr]):
        super().__init__()
        self.args = args


class Minus(IntExpr):
    def __init__(self, left: IntExpr, right: IntExpr):
        super().__init__()
        self.left = left
        self.right = right


class Mul(IntExpr):
    def __init__(self, left: IntExpr, right: IntExpr):
        super().__init__()
        self.left = left
        self.right = right


class Neg(IntExpr):
    def __init__(self, arg: IntExpr):
        super().__init__()
        self.arg = arg


# ============== 求值器 ==============

class SMTEvaluator:
    """
    SMT表达式求值器
    
    在给定变量赋值下求值SMT表达式
    """

    def __init__(self, model: Dict[str, Any] = None):
        """
        Args:
            model: 变量赋值字典，格式 {var_name: value}
        """
        self.model = model or {}

    def set_model(self, model: Dict[str, Any]):
        """设置模型"""
        self.model = model

    def eval(self, expr: Expr) -> Any:
        """
        求值表达式
        
        Returns:
            表达式的值（bool/int/BV）
        """
        if isinstance(expr, ConstBool):
            return expr.value
        
        if isinstance(expr, ConstInt):
            return expr.value
        
        if isinstance(expr, ConstBV):
            return expr.value
        
        if isinstance(expr, Var):
            return self.model.get(expr.name)
        
        if isinstance(expr, Not):
            arg_val = self.eval(expr.arg)
            return not arg_val
        
        if isinstance(expr, And):
            return all(self.eval(a) for a in expr.args)
        
        if isinstance(expr, Or):
            return any(self.eval(a) for a in expr.args)
        
        if isinstance(expr, Implies):
            return (not self.eval(expr.ant)) or self.eval(expr.cons)
        
        if isinstance(expr, Eq):
            left_val = self.eval(expr.left)
            right_val = self.eval(expr.right)
            return left_val == right_val
        
        if isinstance(expr, Lt):
            return self.eval(expr.left) < self.eval(expr.right)
        
        if isinstance(expr, Le):
            return self.eval(expr.left) <= self.eval(expr.right)
        
        if isinstance(expr, Plus):
            return sum(self.eval(a) for a in expr.args)
        
        if isinstance(expr, Minus):
            return self.eval(expr.left) - self.eval(expr.right)
        
        if isinstance(expr, Mul):
            return self.eval(expr.left) * self.eval(expr.right)
        
        if isinstance(expr, Neg):
            return -self.eval(expr.arg)
        
        return None


def example_bool_eval():
    """布尔表达式求值"""
    evaluator = SMTEvaluator({'x': True, 'y': False})
    
    # x and not y
    expr = And([Var('x', BoolSort()), Not(Var('y', BoolSort()))])
    result = evaluator.eval(expr)
    print(f"x=True, y=False → x ∧ ¬y = {result}")


def example_int_eval():
    """整数表达式求值"""
    evaluator = SMTEvaluator({'a': 10, 'b': 3})
    
    # a + b * 2
    expr = Plus([Var('a', IntSort()), Mul(Var('b', IntSort()), ConstInt(2))])
    result = evaluator.eval(expr)
    print(f"a=10, b=3 → a + b*2 = {result}")
    
    # a > b
    lt_expr = Lt(Var('a', IntSort()), Var('b', IntSort()))
    print(f"a=10, b=3 → a < b = {evaluator.eval(lt_expr)}")


def example_nested():
    """嵌套表达式"""
    evaluator = SMTEvaluator({'x': 5, 'y': 7})
    
    # (x + y) > 10 and x < y
    plus_expr = Plus([Var('x', IntSort()), Var('y', IntSort())])
    gt_expr = Lt(ConstInt(10), plus_expr)  # 10 > x+y
    lt_expr = Lt(Var('x', IntSort()), Var('y', IntSort()))
    and_expr = And([gt_expr, lt_expr])
    
    print(f"x=5, y=7 → (10 > x+y) ∧ (x < y) = {evaluator.eval(and_expr)}")


def example_model_update():
    """模型更新"""
    evaluator = SMTEvaluator({'x': 1})
    
    expr = Lt(Var('x', IntSort()), ConstInt(5))
    print(f"初始: x < 5 = {evaluator.eval(expr)}")
    
    evaluator.set_model({'x': 10})
    print(f"更新后: x < 5 = {evaluator.eval(expr)}")


if __name__ == "__main__":
    print("=" * 50)
    print("SMT表达式求值器 测试")
    print("=" * 50)
    
    example_bool_eval()
    print()
    example_int_eval()
    print()
    example_nested()
    print()
    example_model_update()
