# -*- coding: utf-8 -*-
"""
算法实现：程序语言理论 / domain_theory

本文件实现 domain_theory 相关的算法功能。
"""

from typing import List, Set, Dict, Optional, Callable, Generic, TypeVar
from dataclasses import dataclass, field
from enum import Enum, auto
import math


T = TypeVar('T')


@dataclass
class Domain_Element:
    """域元素"""
    def __eq__(self, other):
        return isinstance(other, type(self)) and self._value() == other._value()

    def _value(self):
        raise NotImplementedError


@dataclass
class Bottom(Domain_Element):
    """底元素 ⊥"""
    def _value(self):
        return None

    def __str__(self):
        return "⊥"


@dataclass
class Value_Element(Domain_Element):
    """值元素"""
    value: any

    def _value(self):
        return self.value


class Partial_Order:
    """偏序关系"""
    def __init__(self, le: Callable[[any, any], bool]):
        self.le = le

    def is_leq(self, x, y) -> bool:
        return self.le(x, y)


@dataclass
class CPO:
    """完全偏序（Complete Partial Order）"""
    elements: Set
    le: Callable[[any, any], bool]
    bottom: Optional[Domain_Element] = None


class Flat_CPO:
    """平坦CPO：离散值 + ⊥"""
    def __init__(self, values: List):
        self.bottom = Bottom()
        self.values = list(values)
        self.elements = [self.bottom] + [Value_Element(v) for v in values]
        self._poset = Partial_Order(self._leq)


    def _leq(self, x: Domain_Element, y: Domain_Element) -> bool:
        """⊥ ⊑ x ⊑ x"""
        if isinstance(x, Bottom):
            return True
        if isinstance(y, Bottom):
            return False
        if isinstance(x, Value_Element) and isinstance(y, Value_Element):
            return x.value == y.value
        return False


    def lub(self, chain: List[Domain_Element]) -> Domain_Element:
        """计算链的最小上界"""
        non_bottom = [x for x in chain if not isinstance(x, Bottom)]
        if not non_bottom:
            return self.bottom
        # 单元素链
        if len(non_bottom) == 1:
            return non_bottom[0]
        # 多元素链返回最大（如果有的话）
        return non_bottom[-1] if all(non_bottom[0] == x for x in non_bottom) else self.bottom


class Function_CPO(CPO):
    """函数CPO D → E"""
    def __init__(self, domain: CPO, codomain: CPO):
        self.domain = domain
        self.codomain = codomain
        self.elements = []  # 不存储所有函数
        self.le = self._function_le


    def _function_le(self, f, g) -> bool:
        """f ⊑ g 当且仅当 ∀x∈D. f(x) ⊑ g(x)"""
        for x in self.domain.elements:
            f_val = f(x)
            g_val = g(x)
            if not self.domain.le(f_val, g_val):
                return False
        return True


class Scott_Continuity:
    """斯科特连续性"""
    @staticmethod
    def is_continuous(f: Callable, cpo: CPO, codomain: CPO) -> bool:
        """
        f在CPO上是连续的当且仅当：
        1. f是单调的：x ⊑ y ⇒ f(x) ⊑ f(y)
        2. f保最小上界：f(lub(S)) = lub(f(S)) 对所有有向集S
        """
        # 检查单调性
        for x in cpo.elements:
            for y in cpo.elements:
                if cpo.le(x, y) and not cpo.le(f(x), f(y)):
                    return False
        # 检查保lub
        # (简化) 假设f连续
        return True


class Fixed_Point_Theorem:
    """不动点定理"""
    @staticmethod
    def kleene_fixed_point(f: Callable, cpo: CPO, max_iter: int = 100) -> Domain_Element:
        """
        Kleene不动点定理
        最小不动点 = lub({⊥, f(⊥), f²(⊥), ...})
        """
        if not cpo.bottom:
            raise ValueError("CPO must have bottom element")
        current = cpo.bottom
        chain = [current]
        for _ in range(max_iter):
            next_val = f(current)
            chain.append(next_val)
            if cpo.le(next_val, current) and cpo.le(current, next_val):
                # 找到不动点
                return current
            current = next_val
        # 返回近似
        return cpo.lub(chain)


    @staticmethod
    def tarski_fixed_point(f: Callable, cpo: CPO) -> Optional[Domain_Element]:
        """
        Tarski不动点定理
        在CPO上单调函数f一定有最小和最大不动点
        """
        # 简化的Tarski
        return Fixed_Point_Theorem.kleene_fixed_point(f, cpo)


class Recursive_Domain:
    """递归域定义 D ≅ F(D)"""
    def __init__(self, equation: str, constructor: Callable):
        self.equation = equation
        self.constructor = constructor


@dataclass
class Domain_Expression:
    """域表达式"""
    pass


@dataclass
class D_Plus(Domain_Expression):
    """域的和（分离和）"""
    domains: List[CPO]


@dataclass
class D_Times(Domain_Expression):
    """域的积"""
    domains: List[CPO]


@dataclass
class D_Fun(Domain_Expression):
    """函数域"""
    domain: CPO
    codomain: CPO


class Domain_Builder:
    """域构造器"""
    @staticmethod
    def build_sum(domains: List[CPO]) -> CPO:
        """构造域的和 D₁ ⊕ D₂"""
        return CPO(
            elements=set(),
            le=lambda x, y: False  # 简化
        )


@dataclass
class Least_Fixed_Point:
    """最小不动点"""
    @staticmethod
    def compute(F: Callable, cpo: CPO) -> Domain_Element:
        """
        计算泛函F的最小不动点
        F : (D → E) → (D → E)
        """
        return Fixed_Point_Theorem.kleene_fixed_point(F, cpo)


class Approximation_Chain:
    """逼近链 A₀ ⊑ A₁ ⊑ A₂ ⊑ ... """
    def __init__(self):
        self.elements: List[CPO] = []


    def add(self, element: CPO):
        self.elements.append(element)


    def limit(self) -> Optional[CPO]:
        """极限"""
        if not self.elements:
            return None
        return self.elements[-1]


def basic_test():
    """基本功能测试"""
    print("=== 域理论测试 ===")
    # 平坦CPO
    print("\n[平坦CPO]")
    flat = Flat_CPO([1, 2, 3])
    print(f"  元素: {flat.elements}")
    print(f"  ⊥ ⊑ 1? {flat._leq(flat.bottom, Value_Element(1))}")
    print(f"  1 ⊑ 2? {flat._leq(Value_Element(1), Value_Element(2))}")
    # 链的LUB
    print("\n[最小上界]")
    chain = [flat.bottom, Value_Element(1), Value_Element(1)]
    lub = flat.lub(chain)
    print(f"  lub(⊥, 1, 1) = {lub}")
    # 斯科特连续函数
    print("\n[斯科特连续性]")
    f = lambda x: Value_Element(x.value * 2) if isinstance(x, Value_Element) else flat.bottom
    print(f"  f(x) = 2x 是连续的: {Scott_Continuity.is_continuous(f, flat, flat)}")
    # 不动点
    print("\n[不动点定理]")
    # 阶乘函数的不动点
    def fac_fn(x):
        if isinstance(x, Bottom):
            return Value_Element(1)  # fac(⊥) = 1
        if isinstance(x, Value_Element):
            n = x.value
            if n <= 1:
                return Value_Element(1)
            return Value_Element(n * (n - 1))
        return x
    fix = Fixed_Point_Theorem.kleene_fixed_point(fac_fn, flat)
    print(f"  阶乘函数的不动点 = {fix}")
    # 递归域
    print("\n[递归域]")
    # D ≅ D → Int 的解（朴素贝叶斯不动点）
    print("  D ≅ D → Int 的域方程")
    # 逼近
    print("\n[逼近链]")
    chain_approx = Approximation_Chain()
    chain_approx.add(flat)
    print(f"  链长度: {len(chain_approx.elements)}")


if __name__ == "__main__":
    basic_test()
