# -*- coding: utf-8 -*-
"""
算法实现：程序语言理论 / abstract_interpretation_types

本文件实现 abstract_interpretation_types 相关的算法功能。
"""

from typing import List, Dict, Set, Tuple, Optional, Generic, TypeVar, Callable
from dataclasses import dataclass, field
from enum import Enum, auto


T = TypeVar('T')


class Abstract_Value:
    """抽象值基类"""
    def join(self, other: 'Abstract_Value') -> 'Abstract_Value':
        """抽象域的并（least upper bound）"""
        raise NotImplementedError

    def meet(self, other: 'Abstract_Value') -> 'Abstract_Value':
        """抽象域的交（greatest lower bound）"""
        raise NotImplementedError

    def le(self, other: 'Abstract_Value') -> bool:
        """抽象域的序 ⊑"""
        raise NotImplementedError


@dataclass
class Type_Abstract_Value(Abstract_Value):
    """类型作为抽象值"""
    types: Set[str] = field(default_factory=set)

    def join(self, other: Abstract_Value) -> 'Type_Abstract_Value':
        if isinstance(other, Type_Abstract_Value):
            return Type_Abstract_Value(self.types | other.types)
        return self

    def meet(self, other: Abstract_Value) -> 'Type_Abstract_Value':
        if isinstance(other, Type_Abstract_Value):
            return Type_Abstract_Value(self.types & other.types)
        return Type_Abstract_Value(set())

    def le(self, other: Abstract_Value) -> bool:
        if isinstance(other, Type_Abstract_Value):
            return self.types <= other.types
        return False

    def __str__(self):
        if not self.types:
            return "⊥"
        return " | ".join(sorted(self.types))


@dataclass
class Sign_Abstract_Value(Abstract_Value):
    """符号抽象值：⊥, -, 0, +, ⊤"""
    value: str  # "bottom", "negative", "zero", "positive", "top"

    def join(self, other: Abstract_Value) -> 'Sign_Abstract_Value':
        if not isinstance(other, Sign_Abstract_Value):
            return self
        order = {"bottom": 0, "negative": 1, "zero": 2, "positive": 3, "top": 4}
        if order[self.value] >= order[other.value]:
            return self
        return other

    def meet(self, other: Abstract_Value) -> 'Sign_Abstract_Value':
        if not isinstance(other, Sign_Abstract_Value):
            return Sign_Abstract_Value("bottom")
        order = {"bottom": 0, "negative": 1, "zero": 2, "positive": 3, "top": 4}
        if order[self.value] <= order[other.value]:
            return self
        return other

    def le(self, other: Abstract_Value) -> bool:
        if not isinstance(other, Sign_Abstract_Value):
            return False
        order = {"bottom": 0, "negative": 1, "zero": 2, "positive": 3, "top": 4}
        return order[self.value] <= order[other.value]


class Interval_Abstract_Value(Abstract_Value):
    """区间抽象值 [l, u]"""
    def __init__(self, lower: int, upper: int):
        self.lower = lower
        self.upper = upper

    def join(self, other: Abstract_Value) -> 'Interval_Abstract_Value':
        if isinstance(other, Interval_Abstract_Value):
            return Interval_Abstract_Value(
                min(self.lower, other.lower),
                max(self.upper, other.upper)
            )
        return self

    def meet(self, other: Abstract_Value) -> 'Interval_Abstract_Value':
        if isinstance(other, Interval_Abstract_Value):
            return Interval_Abstract_Value(
                max(self.lower, other.lower),
                min(self.upper, other.upper)
            )
        return Interval_Abstract_Value(float('-inf'), float('inf'))

    def le(self, other: Abstract_Value) -> bool:
        if isinstance(other, Interval_Abstract_Value):
            return self.lower >= other.lower and self.upper <= other.upper
        return False

    def __str__(self):
        return f"[{self.lower}, {self.upper}]"


@dataclass
class Type_Expression:
    """类型表达式"""
    pass


@dataclass
class T_Num(Type_Expression):
    pass


@dataclass
class T_Bool(Type_Expression):
    pass


@dataclass
class T_Var(Type_Expression):
    name: str


@dataclass
class T_Fun(Type_Expression):
    domain: Type_Expression
    codomain: Type_Expression


class Abstract_Type_System:
    """抽象类型系统"""
    def __init__(self, abstract_domain: Abstract_Value):
        self.domain = abstract_domain


class Galois_Connection:
    """伽罗瓦连接"""
    def __init__(self, concrete_domain: Set, abstract_domain: Abstract_Value,
                 alpha: Callable, gamma: Callable):
        self.concrete = concrete_domain
        self.abstract = abstract_domain
        self.alpha = alpha  # 抽象化函数
        self.gamma = gamma  # 具体化函数


class Type_Absraction_Interpretation:
    """类型的抽象解释"""
    def __init__(self):
        self.abstract_types: Dict[str, Abstract_Value] = {}


    def add_type(self, name: str, abs_val: Abstract_Value):
        """添加抽象类型"""
        self.abstract_types[name] = abs_val


    def join_types(self, t1: str, t2: str) -> Abstract_Value:
        """连接两个抽象类型"""
        v1 = self.abstract_types.get(t1, Type_Abstract_Value(set()))
        v2 = self.abstract_types.get(t2, Type_Abstract_Value(set()))
        return v1.join(v2)


    def widen(self, t1: Abstract_Value, t2: Abstract_Value) -> Abstract_Value:
        """
        加宽操作（用于确保有限时间不动点计算）
        确保区间的单调不递减
        """
        if isinstance(t1, Interval_Abstract_Value) and isinstance(t2, Interval_Abstract_Value):
            lower = t1.lower if t1.lower <= t2.lower else float('-inf')
            upper = t1.upper if t1.upper >= t2.upper else float('inf')
            return Interval_Abstract_Value(lower, upper)
        return t1.join(t2)


@dataclass
class Type_Constraint:
    """类型约束"""
    left: str
    right: str
    op: str  # "=", "<:", "⊑"


class Type_Analysis:
    """类型分析"""
    def __init__(self):
        self.constraints: List[Type_Constraint] = []
        self.type_env: Dict[str, Abstract_Value] = {}


    def add_constraint(self, left: str, right: str, op: str = "="):
        """添加类型约束"""
        self.constraints.append(Type_Constraint(left, right, op))


    def solve(self) -> Dict[str, Abstract_Value]:
        """求解约束"""
        # 简化：使用不动点迭代
        changed = True
        while changed:
            changed = False
            for c in self.constraints:
                if c.op == "=":
                    left_val = self.type_env.get(c.left, Type_Abstract_Value(set()))
                    right_val = self.type_env.get(c.right, Type_Abstract_Value(set()))
                    joined = left_val.join(right_val)
                    if not joined.le(left_val) or not joined.le(right_val):
                        self.type_env[c.left] = joined
                        self.type_env[c.right] = joined
                        changed = True
        return self.type_env


class Sign_Analysis:
    """符号分析（具体实例）"""
    def __init__(self):
        self.env: Dict[str, Sign_Abstract_Value] = {}

    def eval_expr(self, expr) -> Sign_Abstract_Value:
        """求值表达式的符号"""
        if isinstance(expr, int):
            if expr < 0:
                return Sign_Abstract_Value("negative")
            elif expr == 0:
                return Sign_Abstract_Value("zero")
            else:
                return Sign_Abstract_Value("positive")
        elif isinstance(expr, str):
            return self.env.get(expr, Sign_Abstract_Value("top"))
        elif isinstance(expr, tuple) and len(expr) == 3:
            if expr[1] == '+':
                left = self.eval_expr(expr[0])
                right = self.eval_expr(expr[2])
                if left.value == "zero":
                    return right
                if right.value == "zero":
                    return left
                if left.value == "negative" and right.value == "negative":
                    return Sign_Abstract_Value("negative")
                if left.value == "positive" and right.value == "positive":
                    return Sign_Abstract_Value("positive")
                return Sign_Abstract_Value("top")
            elif expr[1] == '*':
                left = self.eval_expr(expr[0])
                right = self.eval_expr(expr[2])
                if left.value == "zero" or right.value == "zero":
                    return Sign_Abstract_Value("zero")
                if left.value == "negative" and right.value == "negative":
                    return Sign_Abstract_Value("positive")
                if left.value == "positive" and right.value == "positive":
                    return Sign_Abstract_Value("positive")
                if left.value == "negative" or right.value == "negative":
                    return Sign_Abstract_Value("negative")
                return Sign_Abstract_Value("top")
        return Sign_Abstract_Value("top")

    def assign(self, var: str, expr):
        """赋值语句"""
        self.env[var] = self.eval_expr(expr)


def basic_test():
    """基本功能测试"""
    print("=== 类型抽象解释测试 ===")
    # 抽象类型值
    print("\n[抽象类型值]")
    t1 = Type_Abstract_Value({"Int", "Float"})
    t2 = Type_Abstract_Value({"Float", "String"})
    print(f"  {{Int, Float} ⊔ {{Float, String}} = {t1.join(t2)}")
    print(f"  {{Int, Float} ⊓ {{Float, String}} = {t1.meet(t2)}")
    # 符号抽象值
    print("\n[符号抽象值]")
    neg = Sign_Abstract_Value("negative")
    pos = Sign_Abstract_Value("positive")
    zero = Sign_Abstract_Value("zero")
    print(f"  negative ⊔ positive = {neg.join(pos).value}")
    print(f"  negative ⊓ positive = {neg.meet(pos).value}")
    # 区间抽象值
    print("\n[区间抽象值]")
    i1 = Interval_Abstract_Value(0, 10)
    i2 = Interval_Abstract_Value(5, 15)
    print(f"  [0,10] ⊔ [5,15] = {i1.join(i2)}")
    print(f"  [0,10] ⊓ [5,15] = {i1.meet(i2)}")
    # 加宽
    print("\n[加宽操作]")
    i3 = Interval_Abstract_Value(0, 10)
    i4 = Interval_Abstract_Value(20, 30)
    widened = i3.join(i4)  # 简化
    print(f"  [0,10] ⊔ [20,30] = {widened}")
    # 符号分析
    print("\n[符号分析]")
    analysis = Sign_Analysis()
    analysis.assign("x", 5)
    analysis.assign("y", -3)
    result = analysis.eval_expr(("x", "+", "y"))
    print(f"  x=5, y=-3, x+y = {result.value}")
    analysis.assign("z", ("x", "*", "y"))
    result_z = analysis.env.get("z")
    print(f"  z = x*y = {result_z.value if result_z else 'unknown'}")
    # 复杂表达式
    print("\n[复杂表达式符号分析]")
    analysis2 = Sign_Analysis()
    analysis2.assign("a", ("b", "+", 1))
    print(f"  a = b + 1 的符号")


if __name__ == "__main__":
    basic_test()
