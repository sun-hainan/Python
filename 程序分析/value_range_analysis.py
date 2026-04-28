# -*- coding: utf-8 -*-
"""
值域分析（Value Range Analysis）
功能：分析变量的可能取值范围，用于错误检测和优化

与区间分析的关系：
- 区间分析：数值变量的上下界
- 值域分析：更一般的值集合表示

表示方法：
1. 区间 [lower, upper]
2. 枚举集合 {v1, v2, ...}
3. 谓词抽象 (x > 0)

作者：Value Range Analysis Team
"""

from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict


class ValueRange:
    """
    值域表示
    
    支持多种表示：
    - 单值
    - 有限集合
    - 区间
    - 符号谓词
    """

    def __init__(self, rep_type: str = 'top', **kwargs):
        """
        Args:
            rep_type: 'top', 'bottom', 'interval', 'set', 'constant', 'predicate'
        """
        self.rep_type = rep_type
        self.lower = kwargs.get('lower')
        self.upper = kwargs.get('upper')
        self.values = kwargs.get('values')  # 枚举集合
        self.predicate = kwargs.get('predicate')  # 符号谓词
        self.constant = kwargs.get('constant')

    @staticmethod
    def top() -> 'ValueRange':
        return ValueRange('top')

    @staticmethod
    def bottom() -> 'ValueRange':
        return ValueRange('bottom')

    @staticmethod
    def constant(val: int) -> 'ValueRange':
        return ValueRange('constant', constant=val)

    @staticmethod
    def interval(lower: int, upper: int) -> 'ValueRange':
        return ValueRange('interval', lower=lower, upper=upper)

    @staticmethod
    def set(values: Set[int]) -> 'ValueRange':
        return ValueRange('set', values=values)

    def is_top(self) -> bool:
        return self.rep_type == 'top'

    def is_bottom(self) -> bool:
        return self.rep_type == 'bottom'

    def is_constant(self) -> bool:
        return self.rep_type == 'constant'

    def get_constant(self) -> Optional[int]:
        return self.constant if self.is_constant() else None

    def may_contain(self, val: int) -> bool:
        """检查值是否可能属于此域"""
        if self.is_top():
            return True
        if self.is_bottom():
            return False
        if self.is_constant():
            return self.constant == val
        if self.rep_type == 'interval':
            return self.lower <= val <= self.upper
        if self.rep_type == 'set':
            return val in self.values
        return True

    def join(self, other: 'ValueRange') -> 'ValueRange':
        """
        Join (∪)：合并两个值域（上近似）
        """
        if self.is_top() or other.is_top():
            return ValueRange.top()
        if self.is_bottom():
            return other
        if other.is_bottom():
            return self
        if self.is_constant() and other.is_constant():
            if self.constant == other.constant:
                return self
            return ValueRange.top()
        if self.is_constant() and other.rep_type == 'interval':
            if other.lower <= self.constant <= other.upper:
                return other
            return ValueRange.interval(
                min(self.constant, other.lower),
                max(self.constant, other.upper)
            )
        if self.rep_type == 'interval' and other.is_constant():
            if self.lower <= other.constant <= self.upper:
                return self
            return ValueRange.interval(
                min(self.lower, other.constant),
                max(self.upper, other.constant)
            )
        if self.rep_type == 'interval' and other.rep_type == 'interval':
            return ValueRange.interval(
                min(self.lower, other.lower),
                max(self.upper, other.upper)
            )
        if self.rep_type == 'set' and other.rep_type == 'set':
            return ValueRange.set(self.values | other.values)
        return ValueRange.top()

    def meet(self, other: 'ValueRange') -> 'ValueRange':
        """
        Meet (∩)：两个值域的交集
        """
        if self.is_bottom() or other.is_bottom():
            return ValueRange.bottom()
        if self.is_top():
            return other
        if other.is_top():
            return self
        if self.is_constant() and other.is_constant():
            if self.constant == other.constant:
                return self
            return ValueRange.bottom()
        if self.is_constant() and other.rep_type == 'interval':
            if other.lower <= self.constant <= other.upper:
                return self
            return ValueRange.bottom()
        if self.rep_type == 'interval' and other.is_constant():
            if self.lower <= other.constant <= self.upper:
                return other
            return ValueRange.bottom()
        if self.rep_type == 'interval' and other.rep_type == 'interval':
            new_lower = max(self.lower, other.lower)
            new_upper = min(self.upper, other.upper)
            if new_lower > new_upper:
                return ValueRange.bottom()
            return ValueRange.interval(new_lower, new_upper)
        if self.rep_type == 'set' and other.rep_type == 'set':
            intersection = self.values & other.values
            if not intersection:
                return ValueRange.bottom()
            return ValueRange.set(intersection)
        return ValueRange.top()

    def __repr__(self):
        if self.is_top():
            return "⊤"
        if self.is_bottom():
            return "⊥"
        if self.is_constant():
            return str(self.constant)
        if self.rep_type == 'interval':
            return f"[{self.lower}, {self.upper}]"
        if self.rep_type == 'set':
            return str(self.values)
        return "?"


class ValueRangeAnalysis:
    """
    值域分析器
    """

    def __init__(self):
        self.var_ranges: Dict[str, ValueRange] = {}

    def set_range(self, var: str, range_: ValueRange):
        """设置变量的值域"""
        self.var_ranges[var] = range_

    def get_range(self, var: str) -> ValueRange:
        """获取变量的值域"""
        return self.var_ranges.get(var, ValueRange.top())

    def assign_constant(self, var: str, const: int):
        """赋值常量"""
        self.var_ranges[var] = ValueRange.constant(const)

    def assign_interval(self, var: str, lower: int, upper: int):
        """赋值区间"""
        self.var_ranges[var] = ValueRange.interval(lower, upper)

    def assign_join(self, var: str, ranges: List[ValueRange]):
        """Phi节点：合并多个值域"""
        if not ranges:
            return
        result = ranges[0]
        for r in ranges[1:]:
            result = result.join(r)
        self.var_ranges[var] = result

    def may_be_equal(self, var: str, val: int) -> bool:
        """检查变量是否可能等于某值"""
        return self.get_range(var).may_contain(val)

    def must_be_equal(self, var: str, val: int) -> bool:
        """检查变量是否必定等于某值"""
        r = self.get_range(var)
        if r.is_constant():
            return r.constant == val
        return False

    def check_bounds(self, var: str, lower: int, upper: int) -> Tuple[bool, bool]:
        """
        检查变量边界
        
        Returns:
            (may_be_in_bounds, must_be_in_bounds)
        """
        r = self.get_range(var)
        
        if r.is_bottom():
            return False, False
        
        if r.is_constant():
            in_bounds = lower <= r.constant <= upper
            return in_bounds, in_bounds
        
        if r.rep_type == 'interval':
            may = r.lower <= upper and r.upper >= lower
            must = r.lower >= lower and r.upper <= upper
            return may, must
        
        return True, False  # top：可能但不确定


def example_constant_propagation():
    """常量传播结果的值域"""
    analysis = ValueRangeAnalysis()
    
    # x = 42
    analysis.assign_constant('x', 42)
    
    # y = x + 1
    x_range = analysis.get_range('x')
    if x_range.is_constant():
        analysis.assign_constant('y', x_range.constant + 1)
    
    print(f"x ∈ {analysis.get_range('x')}")
    print(f"y ∈ {analysis.get_range('y')}")
    print(f"x必定等于42: {analysis.must_be_equal('x', 42)}")
    print(f"x可能等于0: {analysis.may_be_equal('x', 0)}")


def example_join_analysis():
    """分支合并的值域"""
    analysis = ValueRangeAnalysis()
    
    # 分支1: x ∈ [1, 10]
    # 分支2: x ∈ [5, 15]
    range1 = ValueRange.interval(1, 10)
    range2 = ValueRange.interval(5, 15)
    
    joined = range1.join(range2)
    met = range1.meet(range2)
    
    print(f"[1,10] ⊔ [5,15] = {joined}")
    print(f"[1,10] ⊓ [5,15] = {met}")


def example_branch_analysis():
    """分支条件分析"""
    analysis = ValueRangeAnalysis()
    
    # x ∈ [0, 100]
    analysis.assign_interval('x', 0, 100)
    
    # if (x > 50) { ... }
    # then分支: x ∈ [51, 100]
    # else分支: x ∈ [0, 50]
    
    then_range = analysis.get_range('x').meet(ValueRange.interval(51, 100))
    else_range = analysis.get_range('x').meet(ValueRange.interval(0, 50))
    
    print(f"分支前: x ∈ {analysis.get_range('x')}")
    print(f"then分支: x ∈ {then_range}")
    print(f"else分支: x ∈ {else_range}")


def example_bounds_check():
    """数组边界检查"""
    analysis = ValueRangeAnalysis()
    
    # n ∈ [1, 100]
    analysis.assign_interval('n', 1, 100)
    
    # 检查: 0 <= n-1 < n
    n_range = analysis.get_range('n')
    
    if n_range.rep_type == 'interval':
        idx_upper = n_range.upper - 1
        print(f"n-1的上界: {idx_upper}")
        
        may_out_of_bounds = idx_upper >= n_range.upper
        print(f"可能越界: {may_out_of_bounds}")


if __name__ == "__main__":
    print("=" * 50)
    print("值域分析 测试")
    print("=" * 50)
    
    example_constant_propagation()
    print()
    example_join_analysis()
    print()
    example_branch_analysis()
    print()
    example_bounds_check()
