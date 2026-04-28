# -*- coding: utf-8 -*-
"""
区间分析（Interval Analysis）
功能：数值变量的值域分析，用于检测数组越界、除零等错误

区间抽象域：
- 每个数值变量用 [lower, upper] 区间表示
- 支持Join（合并区间）和Meet（交集）
- 转换函数处理算术运算

应用：
1. 数组越界检测
2. 循环边界分析
3. 数值稳定性分析

作者：Interval Analysis Team
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict


class Interval:
    """数值区间 [lower, upper]"""
    
    def __init__(self, lower: int, upper: int):
        self.lower = lower
        self.upper = upper
    
    @staticmethod
    def top() -> 'Interval':
        """最坏情况区间（未知）"""
        return Interval(float('-inf'), float('inf'))
    
    @staticmethod
    def bottom() -> 'Interval':
        """矛盾区间（空）"""
        return Interval(float('inf'), float('-inf'))
    
    def is_top(self) -> bool:
        return self.lower == float('-inf') and self.upper == float('inf')
    
    def is_bottom(self) -> bool:
        return self.lower > self.upper
    
    def contains(self, val: int) -> bool:
        """区间是否包含值"""
        return self.lower <= val <= self.upper
    
    def join(self, other: 'Interval') -> 'Interval':
        """
        Join（合并）：取并集的上近似
        [l1,u1] ⊔ [l2,u2] = [min(l1,l2), max(u1,u2)]
        """
        return Interval(min(self.lower, other.lower), 
                        max(self.upper, other.upper))
    
    def meet(self, other: 'Interval') -> 'Interval':
        """
        Meet（相交）：取交集
        [l1,u1] ⊓ [l2,u2] = [max(l1,l2), min(u1,u2)]
        """
        return Interval(max(self.lower, other.lower),
                        min(self.upper, other.upper))
    
    def widen(self, other: 'Interval') -> 'Interval':
        """
        扩展（Widening）：防止无限循环
        若other比self小，则将下界向左扩展，上界向右扩展
        """
        new_lower = self.lower
        new_upper = self.upper
        
        if other.lower < self.lower:
            new_lower = float('-inf')
        if other.upper > self.upper:
            new_upper = float('inf')
        
        return Interval(new_lower, new_upper)
    
    def add(self, other: 'Interval') -> 'Interval':
        """加法：[l1,u1] + [l2,u2] = [l1+l2, u1+u2]"""
        if self.is_bottom() or other.is_bottom():
            return Interval.bottom()
        return Interval(self.lower + other.lower, self.upper + other.upper)
    
    def sub(self, other: 'Interval') -> 'Interval':
        """减法：[l1,u1] - [l2,u2] = [l1-u2, u1-l2]"""
        if self.is_bottom() or other.is_bottom():
            return Interval.bottom()
        return Interval(self.lower - other.upper, self.upper - other.lower)
    
    def mul(self, other: 'Interval') -> 'Interval':
        """乘法：枚举所有组合"""
        if self.is_bottom() or other.is_bottom():
            return Interval.bottom()
        vals = [
            self.lower * other.lower,
            self.lower * other.upper,
            self.upper * other.lower,
            self.upper * other.upper
        ]
        return Interval(min(vals), max(vals))
    
    def div(self, other: 'Interval') -> 'Interval':
        """除法（简化：假设非零）"""
        if self.is_bottom() or other.is_bottom():
            return Interval.bottom()
        if other.contains(0):
            return Interval.top()  # 保守处理
        vals = [
            self.lower / other.lower,
            self.lower / other.upper,
            self.upper / other.lower,
            self.upper / other.upper
        ]
        return Interval(min(vals), max(vals))
    
    def compare_lt(self, other: 'Interval') -> Optional[bool]:
        """
        区间比较 x < y
        
        Returns:
            True: 必定小于
            False: 必定不小于
            None: 可能小于
        """
        if self.is_bottom() or other.is_bottom():
            return None
        if self.upper < other.lower:
            return True
        if self.lower >= other.upper:
            return False
        return None

    def compare_le(self, other: 'Interval') -> Optional[bool]:
        """区间比较 x <= y"""
        if self.is_bottom() or other.is_bottom():
            return None
        if self.upper <= other.lower:
            return True
        if self.lower > other.upper:
            return False
        return None
    
    def __repr__(self):
        if self.is_bottom():
            return "⊥"
        if self.is_top():
            return "⊤"
        return f"[{self.lower}, {self.upper}]"


class IntervalAnalysis:
    """
    区间分析器
    
    对程序中的变量进行区间分析
    """

    def __init__(self):
        # 变量→区间
        self.var_interval: Dict[str, Interval] = {}
        # 循环深度
        self.loop_depth = 0

    def assign(self, var: str, expr_interval: Interval):
        """赋值：var := expr"""
        self.var_interval[var] = expr_interval

    def handle_add(self, var: str, left: Interval, right: Interval):
        """加法赋值"""
        self.var_interval[var] = left.add(right)

    def handle_sub(self, var: str, left: Interval, right: Interval):
        """减法赋值"""
        self.var_interval[var] = left.sub(right)

    def handle_mul(self, var: str, left: Interval, right: Interval):
        """乘法赋值"""
        self.var_interval[var] = left.mul(right)

    def handle_constant(self, var: str, const: int):
        """常量赋值"""
        self.var_interval[var] = Interval(const, const)

    def handle_phi(self, var: str, vals: List[Interval]):
        """Phi函数：合并多个分支的值"""
        if not vals:
            return
        result = vals[0]
        for v in vals[1:]:
            result = result.join(v)
        self.var_interval[var] = result

    def handle_loop_header(self, header_interval: Interval, 
                           current_interval: Interval) -> Interval:
        """循环头处理：应用widening"""
        return header_interval.widen(current_interval)

    def get_interval(self, var: str) -> Interval:
        """获取变量区间"""
        return self.var_interval.get(var, Interval.top())

    def may_be_zero(self, var: str) -> bool:
        """检查变量是否可能为零"""
        interval = self.get_interval(var)
        return interval.contains(0)


class IntervalAnalyzer:
    """
    区间分析框架
    
    分析程序语句，更新区间
    """

    def __init__(self):
        self.analysis = IntervalAnalysis()
        self.changed = False

    def transfer_stmt(self, stmt: Dict, in_state: Dict[str, Interval]) -> Dict[str, Interval]:
        """转换单个语句"""
        out_state = dict(in_state)
        stmt_type = stmt.get('type')
        
        if stmt_type == 'assign':
            lhs = stmt['lhs']
            rhs = stmt['rhs']
            
            if isinstance(rhs, Interval):
                out_state[lhs] = rhs
            elif isinstance(rhs, int):
                out_state[lhs] = Interval(rhs, rhs)
            elif isinstance(rhs, dict):
                result = self._eval_expr(rhs, out_state)
                out_state[lhs] = result
        
        elif stmt_type == 'assume':
            # assume condition
            cond = stmt['cond']
            out_state = self._apply_assume(out_state, cond)
        
        return out_state

    def _eval_expr(self, expr: Dict, state: Dict[str, Interval]) -> Interval:
        """求值表达式"""
        op = expr.get('op')
        
        if op == 'var':
            return state.get(expr['name'], Interval.top())
        
        if op == 'const':
            return Interval(expr['value'], expr['value'])
        
        if op in ('+', '-', '*', '/'):
            left = self._eval_expr(expr['left'], state)
            right = self._eval_expr(expr['right'], state)
            
            if op == '+':
                return left.add(right)
            if op == '-':
                return left.sub(right)
            if op == '*':
                return left.mul(right)
            if op == '/':
                return left.div(right)
        
        return Interval.top()

    def _apply_assume(self, state: Dict[str, Interval], 
                      cond: Dict) -> Dict[str, Interval]:
        """应用assume约束"""
        # 简化处理
        return state


def example_interval_basics():
    """区间基本运算"""
    i1 = Interval(1, 10)
    i2 = Interval(5, 15)
    
    print(f"i1 = {i1}")
    print(f"i2 = {i2}")
    print(f"i1 ⊔ i2 (join) = {i1.join(i2)}")
    print(f"i1 ⊓ i2 (meet) = {i1.meet(i2)}")
    print(f"i1 + i2 = {i1.add(i2)}")
    print(f"i1 * i2 = {i1.mul(i2)}")
    print(f"i1.widen(i2) = {i1.widen(i2)}")


def example_simple_analysis():
    """简单程序分析"""
    analyzer = IntervalAnalyzer()
    
    # x = 0; y = 10;
    # while (y > 0) { x = x + 1; y = y - 1; }
    
    state: Dict[str, Interval] = {
        'x': Interval(0, 0),
        'y': Interval(10, 10),
    }
    
    # 循环前几次迭代
    for i in range(5):
        print(f"迭代 {i}: x ∈ {state.get('x')}, y ∈ {state.get('y')}")
        
        # x = x + 1
        x_old = state['x']
        state['x'] = x_old.add(Interval(1, 1))
        
        # y = y - 1
        y_old = state['y']
        state['y'] = y_old.sub(Interval(1, 1))


def example_bounds_check():
    """边界检查示例"""
    analyzer = IntervalAnalyzer()
    
    # 模拟: x ∈ [0, 100], y ∈ [1, 10]
    # 检查: if (x >= 0 && x < y) - 数组访问 x[y]
    
    state = {
        'x': Interval(0, 100),
        'y': Interval(1, 10),
    }
    
    x = state['x']
    y = state['y']
    
    print(f"x ∈ {x}")
    print(f"y ∈ {y}")
    
    # 检查 x < y
    lt_result = x.compare_lt(y)
    print(f"x < y: {'必定' if lt_result == True else '必定不' if lt_result == False else '可能'}")
    
    # 检查 x >= 0
    ge_result = x.compare_le(Interval(-1, -1))
    print(f"x >= 0: {'必定' if ge_result == False else '可能'}")
    
    # 检查 y > 0
    y_pos = y.compare_lt(Interval(0, 0))
    print(f"y > 0: {'必定' if y_pos == True else '可能'}")


if __name__ == "__main__":
    print("=" * 50)
    print("区间分析 测试")
    print("=" * 50)
    
    example_interval_basics()
    print()
    example_simple_analysis()
    print()
    example_bounds_check()
