# -*- coding: utf-8 -*-
"""
算法实现：程序语言理论 / denotational_semantics

本文件实现 denotational_semantics 相关的算法功能。
"""

from typing import List, Optional, Dict, Callable, Generic, TypeVar, Set
from dataclasses import dataclass, field
from enum import Enum, auto
import math


T = TypeVar('T')
U = TypeVar('U')


class Domain_Element:
    """域元素基类"""
    def __repr__(self):
        return self.__class__.__name__


@dataclass
class Bottom(Domain_Element):
    """底元素 ⊥"""
    def __str__(self):
        return "⊥"


@dataclass
class Value(Domain_Element):
    """值元素"""
    value: any


@dataclass
class Function(Domain_Element):
    """函数元素"""
    f: Callable


class CPO:
    """
    完全偏序（Complete Partial Order）
    CPO是带有最小上界（lub）的偏序集合
    """
    def __init__(self, elements: Set, partial_order: Callable[[any, any], bool]):
        self.elements = elements
        self.le = partial_order  # ≤ 关系
        self._lub_cache: Dict[frozenset, any] = {}


    def is_bottom(self, x) -> bool:
        """检查是否是底元素"""
        for e in self.elements:
            if self.le(e, x) and not self.le(x, e):
                return False
            if self.le(x, e):
                return True
        return False


    def lub(self, chain: Set) -> Optional:
        """最小上界（Least Upper Bound）"""
        if not chain:
            return None
        # 简化：假设链有上界，返回最大值
        return max(chain) if all(isinstance(x, (int, float)) for x in chain) else None


class Flat_Domain(CPO):
    """平坦域：值 + ⊥"""
    def __init__(self, values: List):
        self.values = list(values)
        self.bottom = Bottom()
        all_elements = [self.bottom] + values
        super().__init__(
            set(all_elements),
            lambda x, y: x == y or x == self.bottom
        )
        self.bottom = Bottom()


    def lub(self, chain: Set) -> Optional:
        if not chain:
            return None
        non_bottom = [x for x in chain if not isinstance(x, Bottom)]
        if not non_bottom:
            return self.bottom
        return non_bottom[0] if len(non_bottom) == 1 else non_bottom[-1]


class Function_Domain(CPO):
    """函数域 D -> E"""
    def __init__(self, domain: CPO, codomain: CPO):
        self.domain = domain
        self.codomain = codomain
        self.elements = []  # 不存储所有函数
        super().__init__(
            set(),
            lambda f, g: all(
                domain.le(f(x), g(x)) for x in domain.elements
            ) if hasattr(f, '__call__') and hasattr(g, '__call__') else False
        )


class Scott_Continuity:
    """
    斯科特连续性
    f是连续的当且仅当 f(lub(S)) = lub(f(S)) 对所有有向集S成立
    """
    @staticmethod
    def is_continuous(f: Callable, domain: CPO, codomain: CPO) -> bool:
        """检查函数是否斯科特连续"""
        return True  # 简化


class Fixed_Point:
    """不动点理论"""
    @staticmethod
    def kleene_iteration(f: Callable, bottom, max_iter: int = 100) -> any:
        """
        Kleene不动点迭代
        ⊥, f(⊥), f(f(⊥)), ... -> ⊥ ⊑ f(⊥) ⊑ f²(⊥) ⊑ ...
        """
        current = bottom
        for i in range(max_iter):
            next_val = f(current)
            if current == next_val:
                return current
            current = next_val
        return current  # 近似不动点


    @staticmethod
    def tarski_theorem(f: Callable, cpo: CPO) -> Optional[any]:
        """
        Tarski不动点定理
        在CPO上单调函数f有最小不动点 = lub({⊥, f(⊥), f²(⊥), ...})
        """
        return Fixed_Point.kleene_iteration(f, Bottom(), max_iter=100)


@dataclass
class Denotational_Expr:
    """指称语义表达式"""
    pass


@dataclass
class D_Num(Denotational_Expr):
    """数值"""
    value: int


@dataclass
class D_Bool(Denotational_Expr):
    """布尔值"""
    value: bool


@dataclass
class D_Var(Denotational_Expr):
    """变量"""
    name: str


@dataclass
class D_Abs(Denotational_Expr):
    """λ抽象"""
    var: str
    body: Denotational_Expr


@dataclass
class D_App(Denotational_Expr):
    """函数应用"""
    func: Denotational_Expr
    arg: Denotational_Expr


@dataclass
class D_If(Denotational_Expr):
    """条件"""
    cond: Denotational_Expr
    then_branch: Denotational_Expr
    else_branch: Denotational_Expr


@dataclass
class D_Let(Denotational_Expr):
    """Let绑定"""
    var: str
    value: Denotational_Expr
    body: Denotational_Expr


class Denotational_Semantics:
    """指称语义解释器"""
    def __init__(self):
        self.env: Dict[str, any] = {}
        self.int_domain = Flat_Domain([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.bool_domain = Flat_Domain([True, False])


    def eval(self, expr: Denotational_Expr) -> Domain_Element:
        """求值表达式"""
        if isinstance(expr, D_Num):
            return Value(expr.value)
        elif isinstance(expr, D_Bool):
            return Value(expr.value)
        elif isinstance(expr, D_Var):
            if expr.name in self.env:
                return self.env[expr.name]
            return Bottom()
        elif isinstance(expr, D_Abs):
            # 函数值
            return Function(lambda x: self.eval_with_binding(expr.var, x, expr.body))
        elif isinstance(expr, D_App):
            func_val = self.eval(expr.func)
            arg_val = self.eval(expr.arg)
            if isinstance(func_val, Function):
                return func_val.f(arg_val)
            return Bottom()
        elif isinstance(expr, D_If):
            cond_val = self.eval(expr.cond)
            if isinstance(cond_val, Value) and cond_val.value:
                return self.eval(expr.then_branch)
            else:
                return self.eval(expr.else_branch)
        elif isinstance(expr, D_Let):
            val = self.eval(expr.value)
            old_env = dict(self.env)
            self.env[expr.var] = val
            result = self.eval(expr.body)
            self.env = old_env
            return result
        return Bottom()


    def eval_with_binding(self, var: str, value: any, body: Denotational_Expr) -> any:
        """在绑定变量的情况下求值"""
        old_env = dict(self.env)
        self.env[var] = value
        result = self.eval(body)
        self.env = old_env
        return result


class Recursive_Denotational_Semantics(Denotational_Semantics):
    """支持递归的指称语义"""
    def __init__(self):
        super().__init__()
        self.fix_operator = Fixed_Point()


    def eval_recursive(self, expr: Denotational_Expr) -> Domain_Element:
        """
        对递归表达式求值
        letrec f = λx.e in b  解释为  let f = Y (λf.λx.e) in b
        其中Y是组合子
        """
        return self.eval(expr)


class Domain_Theory_Examples:
    """域理论示例"""
    @staticmethod
    def factorial_semantics():
        """阶乘函数的指称语义"""
        # fac = λn.if n == 0 then 1 else n * fac(n-1)
        # 在域理论中，这对应于不动点方程
        pass


def basic_test():
    """基本功能测试"""
    print("=== 指称语义测试 ===")
    # 平坦域
    print("\n[平坦域]")
    domain = Flat_Domain([0, 1, 2, 3])
    print(f"  域: {domain.elements}")
    print(f"  ⊥ <= 0? {domain.le(domain.bottom, 0)}")
    print(f"  0 <= 1? {domain.le(0, 1)}")
    print(f"  lub(⊥, 0, 1) = {domain.lub({domain.bottom, 0, 1})}")
    # 指称语义解释器
    print("\n[指称语义解释器]")
    interpreter = Denotational_Semantics()
    # 数值
    print(f"  eval(42) = {interpreter.eval(D_Num(42))}")
    print(f"  eval(True) = {interpreter.eval(D_Bool(True))}")
    # 变量
    interpreter.env["x"] = Value(10)
    print(f"  eval(x) with x=10 = {interpreter.eval(D_Var('x'))}")
    # λ抽象和应用
    print("\n[函数应用]")
    abs_expr = D_Abs("n", D_If(
        D_Var("n"),
        D_Num(1),
        D_App(D_App(Var("n"), D_Num(2)), D_Var("n"))  # n * 2
    ))
    app = D_App(abs_expr, D_Num(5))
    # result = interpreter.eval(app)
    # print(f"  eval((λn.if n then 1 else n*2) 5) = {result}")
    # Let绑定
    print("\n[Let绑定]")
    let_expr = D_Let("x", D_Num(10), D_Let("y", D_Num(20), D_App(D_App(Var("+"), D_Var("x")), D_Var("y"))))
    # 需要定义+操作
    # result = interpreter.eval(let_expr)
    # print(f"  eval(let x=10 in let y=20 in x+y) = {result}")
    # 不动点
    print("\n[不动点]")
    def f(x):
        if isinstance(x, Bottom):
            return Value(1)
        elif isinstance(x, Value):
            if x.value == 0:
                return Value(1)
            return Value(x.value * (x.value - 1))
        return x
    fix = Fixed_Point.tarski_theorem(f, Flat_Domain([0, 1, 2, 3, 4, 5]))
    print(f"  阶乘函数的不动点 = {fix}")


if __name__ == "__main__":
    basic_test()
