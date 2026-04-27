# -*- coding: utf-8 -*-
"""
算法实现：程序分析 / abstract_interpretation

本文件实现 abstract_interpretation 相关的算法功能。
"""

from typing import Dict, List, Set, Optional, Tuple, Any
from abc import ABC, abstractmethod
from collections import defaultdict


class AbstractValue(ABC):
    """
    抽象值的基类
    
    定义抽象解释中抽象值的基本接口。
    """
    
    @abstractmethod
    def join(self, other: 'AbstractValue') -> 'AbstractValue':
        """
        并运算 (Join)：计算两个抽象值的最小上界
        
        Args:
            other: 另一个抽象值
            
        Returns:
            最小上界
        """
        pass
    
    @abstractmethod
    def meet(self, other: 'AbstractValue') -> 'AbstractValue':
        """
        交运算 (Meet)：计算两个抽象值的最大下界
        
        Args:
            other: 另一个抽象值
            
        Returns:
            最大下界
        """
        pass
    
    @abstractmethod
    def less_or_equal(self, other: 'AbstractValue') -> bool:
        """
        偏序关系：检查当前抽象值是否小于等于另一个
        
        Args:
            other: 另一个抽象值
            
        Returns:
            如果self <= other则返回True
        """
        pass
    
    @abstractmethod
    def is_bottom(self) -> bool:
        """检查是否为底元素（空集合）"""
        pass
    
    @abstractmethod
    def is_top(self) -> bool:
        """检查是否为顶元素（全体）"""
        pass


class ConstantDomain(AbstractValue):
    """
    常量抽象域
    
    表示变量可能的常量值集合。
    - Top: 未知值
    - Bottom: 无效/不可能的值
    - Constant: 确定的常量值
    - Constants: 可能的常量值集合
    """
    
    def __init__(self, value: Optional[Any] = None, is_top: bool = False):
        """
        初始化常量域
        
        Args:
            value: 常量值，如果为None且不是top表示bottom
            is_top: 是否为top（未知）
        """
        self.value = value      # 常量值
        self.is_top = is_top    # 是否为top
        self.is_bottom = value is None and not is_top  # bottom条件
    
    def join(self, other: 'ConstantDomain') -> 'ConstantDomain':
        """并运算：如果值相同则保持，否则变为top"""
        if self.is_top or other.is_top:
            return ConstantDomain(is_top=True)
        if self.is_bottom:
            return other
        if other.is_bottom:
            return self
        if self.value == other.value:
            return ConstantDomain(self.value)
        return ConstantDomain(is_top=True)
    
    def meet(self, other: 'ConstantDomain') -> 'ConstantDomain':
        """交运算：如果值相同则保持，否则变为bottom"""
        if self.is_top:
            return other
        if other.is_top:
            return self
        if self.is_bottom or other.is_bottom:
            return ConstantDomain()  # bottom
        if self.value == other.value:
            return ConstantDomain(self.value)
        return ConstantDomain()  # bottom
    
    def less_or_equal(self, other: 'ConstantDomain') -> bool:
        """偏序关系"""
        if self.is_bottom:
            return True
        if self.is_top:
            return other.is_top
        if other.is_top:
            return True
        if other.is_bottom:
            return False
        return self.value == other.value
    
    def is_bottom(self) -> bool:
        return self.is_bottom
    
    def is_top(self) -> bool:
        return self.is_top
    
    def __repr__(self):
        if self.is_top:
            return "⊤"
        if self.is_bottom:
            return "⊥"
        return f"{self.value}"


class IntervalDomain(AbstractValue):
    """
    区间抽象域
    
    表示变量的取值范围。
    - [a, b] 表示变量值在a到b之间
    - Top 表示整个整数域
    - Bottom 表示空集
    """
    
    def __init__(self, lower: Optional[int] = None, upper: Optional[int] = None):
        """
        初始化区间域
        
        Args:
            lower: 下界，None表示负无穷
            upper: 上界，None表示正无穷
        """
        self.lower = lower  # 下界
        self.upper = upper  # 上界
        # 自动判断top和bottom
        if lower is None and upper is None:
            self.is_top = True
            self.is_bottom = False
        elif lower is not None and upper is not None and lower > upper:
            self.is_top = False
            self.is_bottom = True
        else:
            self.is_top = False
            self.is_bottom = False
    
    @staticmethod
    def top() -> 'IntervalDomain':
        """创建top元素"""
        return IntervalDomain()
    
    @staticmethod
    def bottom() -> 'IntervalDomain':
        """创建bottom元素"""
        return IntervalDomain(1, 0)  # 1 > 0 表示空
    
    def join(self, other: 'IntervalDomain') -> 'IntervalDomain':
        """并运算：取两个区间的并集（最小上界）"""
        if self.is_top or other.is_top:
            return IntervalDomain.top()
        if self.is_bottom:
            return other
        if other.is_bottom:
            return self
        
        new_lower = min(self.lower, other.lower) if self.lower is not None and other.lower is not None else (self.lower if self.lower is not None else other.lower)
        new_upper = max(self.upper, other.upper) if self.upper is not None and other.upper is not None else (self.upper if self.upper is not None else other.upper)
        
        return IntervalDomain(new_lower, new_upper)
    
    def meet(self, other: 'IntervalDomain') -> 'IntervalDomain':
        """交运算：取两个区间的交集（最大下界）"""
        if self.is_bottom or other.is_bottom:
            return IntervalDomain.bottom()
        
        if self.is_top:
            return other
        if other.is_top:
            return self
        
        new_lower = max(self.lower, other.lower) if self.lower is not None and other.lower is not None else (other.lower if self.lower is None else self.lower)
        new_upper = min(self.upper, other.upper) if self.upper is not None and other.upper is not None else (other.upper if self.upper is None else self.upper)
        
        if new_lower is not None and new_upper is not None and new_lower > new_upper:
            return IntervalDomain.bottom()
        
        return IntervalDomain(new_lower, new_upper)
    
    def less_or_equal(self, other: 'IntervalDomain') -> bool:
        """偏序关系：self ⊑ other 当且仅当 other 的区间包含 self"""
        if self.is_bottom:
            return True
        if self.is_top:
            return other.is_top
        if other.is_bottom:
            return False
        if other.is_top:
            return True
        
        if self.lower is not None and other.lower is not None and self.lower < other.lower:
            return False
        if self.upper is not None and other.upper is not None and self.upper > other.upper:
            return False
        return True
    
    def is_bottom(self) -> bool:
        return self.is_bottom
    
    def is_top(self) -> bool:
        return self.is_top
    
    def __repr__(self):
        if self.is_top:
            return "[-∞, +∞]"
        if self.is_bottom:
            return "⊥"
        lower_str = str(self.lower) if self.lower is not None else "-∞"
        upper_str = str(self.upper) if self.upper is not None else "+∞"
        return f"[{lower_str}, {upper_str}]"


class SignDomain(AbstractValue):
    """
    符号抽象域
    
    表示数值的符号：正、负、零。
    - ⊤: 未知/任意
    - ⊥: 不可能
    - +: 正数
    - -: 负数
    - 0: 零
    - +-: 非负（正或零）
    - -+: 非正（负或零）
    """
    
    # 符号值枚举
    TOP = "⊤"      # 任意值
    BOTTOM = "⊥"   # 不可能
    POSITIVE = "+"     # 正数
    NEGATIVE = "-"     # 负数
    ZERO = "0"        # 零
    NON_NEGATIVE = "+-"  # 非负
    NON_POSITIVE = "-+"  # 非正
    
    def __init__(self, sign: str = None):
        """
        初始化符号域
        
        Args:
            sign: 符号值，默认为TOP（未知）
        """
        if sign is None:
            sign = self.TOP
        self.sign = sign
        
        self.is_top = sign == self.TOP
        self.is_bottom = sign == self.BOTTOM
    
    def join(self, other: 'SignDomain') -> 'SignDomain':
        """并运算：合并符号信息"""
        if self.is_top or other.is_top:
            return SignDomain(self.TOP)
        if self.is_bottom:
            return other
        if other.is_bottom:
            return self
        
        # 合并符号
        combined = self._merge_signs(self.sign, other.sign)
        return SignDomain(combined)
    
    def meet(self, other: 'SignDomain') -> 'SignDomain':
        """交运算：交集"""
        if self.is_bottom or other.is_bottom:
            return SignDomain(self.BOTTOM)
        
        if self.is_top:
            return other
        if other.is_top:
            return self
        
        # 求交集
        combined = self._intersect_signs(self.sign, other.sign)
        if combined == "":
            return SignDomain(self.BOTTOM)
        return SignDomain(combined)
    
    def _merge_signs(self, s1: str, s2: str) -> str:
        """合并两个符号集合"""
        combined = set(s1) | set(s2)
        if "+" in combined and "-" in combined and "0" in combined:
            return self.TOP
        if "+" in combined and "-" in combined:
            return "+-"
        if "+" in combined and "0" in combined:
            return "+-"
        if "-" in combined and "0" in combined:
            return "-+"
        if "+" in combined:
            return "+"
        if "-" in combined:
            return "-"
        if "0" in combined:
            return "0"
        return self.TOP
    
    def _intersect_signs(self, s1: str, s2: str) -> str:
        """求两个符号集合的交集"""
        combined = set(s1) & set(s2)
        if not combined:
            return ""
        result = "".join(sorted(combined))
        # 简化表示
        if result == "+0" or result == "0+":
            return "+-"
        if result == "-0" or result == "0-":
            return "-+"
        return result
    
    def less_or_equal(self, other: 'SignDomain') -> bool:
        """偏序关系"""
        if self.is_bottom:
            return True
        if self.is_top:
            return other.is_top
        
        if other.is_top:
            return True
        if other.is_bottom:
            return False
        
        # self ⊑ other 意味着 other 包含 self 的所有符号
        return set(self.sign).issubset(set(other.sign))
    
    def is_bottom(self) -> bool:
        return self.is_bottom
    
    def is_top(self) -> bool:
        return self.is_top
    
    def __repr__(self):
        return self.sign


class AbstractInterpreter:
    """
    抽象解释器基类
    
    使用抽象域对程序进行静态分析。
    """
    
    def __init__(self, abstract_domain_class):
        """
        初始化抽象解释器
        
        Args:
            abstract_domain_class: 抽象域类
        """
        self.abstract_domain_class = abstract_domain_class
        # 程序点的抽象状态：program_point -> {variable -> AbstractValue}
        self.state: Dict[int, Dict[str, AbstractValue]] = defaultdict(dict)
        # 入口状态
        self.entry_state: Dict[str, AbstractValue] = {}
    
    def set_entry_value(self, var: str, value: AbstractValue):
        """
        设置变量的入口值
        
        Args:
            var: 变量名
            value: 抽象值
        """
        self.entry_state[var] = value
    
    def get_state(self, point: int) -> Dict[str, AbstractValue]:
        """
        获取指定程序点的状态
        
        Args:
            point: 程序点编号
            
        Returns:
            变量到抽象值的映射
        """
        return self.state.get(point, {})
    
    def assign(self, point: int, var: str, value: AbstractValue):
        """
        执行赋值语句的抽象解释
        
        Args:
            point: 程序点
            var: 目标变量
            value: 抽象值
        """
        current_state = self.get_state(point)
        current_state[var] = value
        self.state[point] = current_state
    
    def eval_expr(self, expr: str, state: Dict[str, AbstractValue]) -> AbstractValue:
        """
        评估表达式的抽象值
        
        Args:
            expr: 表达式字符串
            state: 当前抽象状态
            
        Returns:
            表达式的抽象值
        """
        # 这是一个简化实现
        # 实际实现需要解析表达式并应用抽象运算
        
        expr = expr.strip()
        
        # 检查是否是数字常量
        try:
            num = int(expr)
            if self.abstract_domain_class == IntervalDomain:
                return IntervalDomain(num, num)
            elif self.abstract_domain_class == ConstantDomain:
                return ConstantDomain(num)
            elif self.abstract_domain_class == SignDomain:
                if num > 0:
                    return SignDomain(SignDomain.POSITIVE)
                elif num < 0:
                    return SignDomain(SignDomain.NEGATIVE)
                else:
                    return SignDomain(SignDomain.ZERO)
        except ValueError:
            pass
        
        # 检查是否是变量
        if expr in state:
            return state[expr]
        
        # 处理二元运算
        for op in ['+', '-', '*', '/']:
            if op in expr:
                parts = expr.split(op)
                if len(parts) == 2:
                    left = self.eval_expr(parts[0], state)
                    right = self.eval_expr(parts[1], state)
                    
                    if self.abstract_domain_class == IntervalDomain:
                        return self._interval_arith(left, right, op)
                    elif self.abstract_domain_class == SignDomain:
                        return self._sign_arith(left, right, op)
        
        # 默认返回top
        if self.abstract_domain_class == IntervalDomain:
            return IntervalDomain.top()
        elif self.abstract_domain_class == SignDomain:
            return SignDomain(SignDomain.TOP)
        else:
            return ConstantDomain(is_top=True)
    
    def _interval_arith(self, left: IntervalDomain, right: IntervalDomain, op: str) -> IntervalDomain:
        """区间算术运算"""
        if left.is_top or right.is_top:
            return IntervalDomain.top()
        if left.is_bottom or right.is_bottom:
            return IntervalDomain.bottom()
        
        if op == '+':
            l = left.lower + right.lower if left.lower is not None and right.lower is not None else None
            u = left.upper + right.upper if left.upper is not None and right.upper is not None else None
            return IntervalDomain(l, u)
        elif op == '-':
            l = left.lower - right.upper if left.lower is not None and right.upper is not None else None
            u = left.upper - right.lower if left.upper is not None and right.lower is not None else None
            return IntervalDomain(l, u)
        
        return IntervalDomain.top()
    
    def _sign_arith(self, left: SignDomain, right: SignDomain, op: str) -> SignDomain:
        """符号算术运算"""
        if left.is_top or right.is_top:
            return SignDomain(SignDomain.TOP)
        if left.is_bottom or right.is_bottom:
            return SignDomain(SignDomain.BOTTOM)
        
        # 简化的符号运算
        if op == '+':
            if left.sign == SignDomain.NEGATIVE and right.sign == SignDomain.NEGATIVE:
                return SignDomain(SignDomain.NEGATIVE)
            elif left.sign == SignDomain.POSITIVE and right.sign == SignDomain.POSITIVE:
                return SignDomain(SignDomain.POSITIVE)
            return SignDomain(SignDomain.TOP)
        elif op == '*':
            if left.sign == SignDomain.ZERO or right.sign == SignDomain.ZERO:
                return SignDomain(SignDomain.ZERO)
            elif left.sign == right.sign:
                return SignDomain(SignDomain.POSITIVE)
            else:
                return SignDomain(SignDomain.NEGATIVE)
        
        return SignDomain(SignDomain.TOP)
    
    def display_state(self):
        """显示抽象解释状态"""
        print("=" * 60)
        print("Abstract Interpretation State")
        print("=" * 60)
        
        for point in sorted(self.state.keys()):
            print(f"\nProgram Point {point}:")
            state = self.state[point]
            for var, value in sorted(state.items()):
                print(f"  {var} = {value}")


if __name__ == "__main__":
    print("=" * 60)
    print("测试1：区间域抽象解释")
    print("=" * 60)
    
    interpreter = AbstractInterpreter(IntervalDomain)
    
    # x = 5
    interpreter.assign(0, "x", IntervalDomain(5, 5))
    # y = 10
    interpreter.assign(1, "y", IntervalDomain(10, 10))
    # z = x + y
    state_1 = interpreter.get_state(1)
    z_val = interpreter.eval_expr("x + y", state_1)
    interpreter.assign(2, "z", z_val)
    
    interpreter.display_state()
    
    print("\n" + "=" * 60)
    print("测试2：符号域抽象解释")
    print("=" * 60)
    
    sign_interpreter = AbstractInterpreter(SignDomain)
    
    # a = -5
    sign_interpreter.assign(0, "a", SignDomain(SignDomain.NEGATIVE))
    # b = 10
    sign_interpreter.assign(1, "b", SignDomain(SignDomain.POSITIVE))
    # c = a * b
    state_1 = sign_interpreter.get_state(1)
    c_val = sign_interpreter.eval_expr("a * b", state_1)
    sign_interpreter.assign(2, "c", c_val)
    
    sign_interpreter.display_state()
    
    print("\n" + "=" * 60)
    print("测试3：常量域抽象解释")
    print("=" * 60)
    
    const_interpreter = AbstractInterpreter(ConstantDomain)
    
    # x = 5
    const_interpreter.assign(0, "x", ConstantDomain(5))
    # y = 5
    const_interpreter.assign(1, "y", ConstantDomain(5))
    # z = x + y (应该仍然是常量)
    state_1 = const_interpreter.get_state(1)
    z_val = const_interpreter.eval_expr("x + y", state_1)
    const_interpreter.assign(2, "z", z_val)
    
    const_interpreter.display_state()
    
    print("\n" + "=" * 60)
    print("测试4：区间域的Join和Meet")
    print("=" * 60)
    
    # 区间 [1, 5] 和 [3, 7] 的合并
    int1 = IntervalDomain(1, 5)
    int2 = IntervalDomain(3, 7)
    
    joined = int1.join(int2)
    met = int1.meet(int2)
    
    print(f"  [1,5] ⊔ [3,7] = {joined}")
    print(f"  [1,5] ⊓ [3,7] = {met}")
    
    print("\n抽象解释测试完成!")
