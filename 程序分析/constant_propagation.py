# -*- coding: utf-8 -*-
"""
常量传播分析（Constant Propagation）
功能：确定变量在程序各点的常量值

数据流分析实例：
- 方向：前向
- 格：常量格 ⊤ (未知) / ⊥ (非常量或无定义) / {v} (常量值)
- Meet操作：⊔ (join，常量时相等取常量，否则⊤)

作者：Constant Propagation Team
"""

from typing import List, Dict, Set, Tuple, Optional, Any
from enum import Enum


class ConstValue(Enum):
    """常量值枚举"""
    UNDEF = 0      # 未定义
    NAC = 1        # Not A Constant（非常量）
    CONST = 2      # 常量


class LatticeValue:
    """常量格值"""
    
    def __init__(self, const_type: ConstValue = ConstValue.UNDEF, value: Any = None):
        self.const_type = const_type
        self.value = value

    @staticmethod
    def top():
        return LatticeValue(ConstValue.NAC)  # NAC = top (未知)

    @staticmethod
    def bottom():
        return LatticeValue(ConstValue.UNDEF)  # UNDEF = bottom

    @staticmethod
    def constant(val: Any):
        return LatticeValue(ConstValue.CONST, val)

    def is_top(self) -> bool:
        return self.const_type == ConstValue.NAC

    def is_bottom(self) -> bool:
        return self.const_type == ConstValue.UNDEF

    def is_constant(self) -> bool:
        return self.const_type == ConstValue.CONST

    def get_constant(self) -> Optional[Any]:
        return self.value if self.is_constant() else None

    def join(self, other: 'LatticeValue') -> 'LatticeValue':
        """
        Join操作：⊔
        
        - ⊤ ⊔ x = ⊤
        - ⊥ ⊔ x = x
        - c ⊔ c = c
        - c ⊔ d = ⊤ (c ≠ d)
        """
        if self.is_top() or other.is_top():
            return LatticeValue.top()
        if self.is_bottom():
            return other
        if other.is_bottom():
            return self
        if self.is_constant() and other.is_constant():
            if self.value == other.value:
                return self
            return LatticeValue.top()
        return LatticeValue.top()

    def meet(self, other: 'LatticeValue') -> 'LatticeValue':
        """
        Meet操作：⊓
        
        - ⊤ ⊓ x = x
        - ⊥ ⊓ x = ⊥
        - c ⊓ c = c
        - c ⊓ d = ⊥ (c ≠ d)
        """
        if self.is_bottom() or other.is_bottom():
            return LatticeValue.bottom()
        if self.is_top():
            return other
        if other.is_top():
            return self
        if self.is_constant() and other.is_constant():
            if self.value == other.value:
                return self
            return LatticeValue.bottom()
        return LatticeValue.top()

    def __repr__(self):
        if self.is_top():
            return "NAC"
        if self.is_bottom():
            return "UNDEF"
        return f"{self.value}"


class ConstantPropagation:
    """
    常量传播分析
    
    使用数据流框架
    """

    def __init__(self):
        self.var_value: Dict[str, LatticeValue] = {}

    def evaluate_expr(self, expr: Dict, env: Dict[str, LatticeValue]) -> LatticeValue:
        """
        求值表达式
        
        Args:
            expr: 表达式字典
            env: 当前变量值映射
            
        Returns:
            表达式的常量值
        """
        if isinstance(expr, (int, float, str)) and not isinstance(expr, str):
            return LatticeValue.constant(expr)
        
        if isinstance(expr, str):
            return env.get(expr, LatticeValue.top())
        
        if isinstance(expr, dict):
            op = expr.get('op')
            
            if op in ('+', '-', '*', '/'):
                left = self.evaluate_expr(expr['left'], env)
                right = self.evaluate_expr(expr['right'], env)
                return self._compute_binop(op, left, right)
            
            if op == 'var':
                return env.get(expr['name'], LatticeValue.top())
            
            if op == 'const':
                return LatticeValue.constant(expr['value'])
        
        return LatticeValue.top()

    def _compute_binop(self, op: str, left: LatticeValue, right: LatticeValue) -> LatticeValue:
        """计算二元操作"""
        if not (left.is_constant() and right.is_constant()):
            return LatticeValue.top()
        
        l, r = left.value, right.value
        
        try:
            if op == '+':
                return LatticeValue.constant(l + r)
            if op == '-':
                return LatticeValue.constant(l - r)
            if op == '*':
                return LatticeValue.constant(l * r)
            if op == '/':
                if r == 0:
                    return LatticeValue.top()
                return LatticeValue.constant(l // r)
        except:
            pass
        
        return LatticeValue.top()

    def transfer(self, stmt: Dict, in_env: Dict[str, LatticeValue]) -> Dict[str, LatticeValue]:
        """
        转换函数
        
        Args:
            stmt: 语句
            in_env: 输入环境
            
        Returns:
            输出环境
        """
        out_env = dict(in_env)
        stmt_type = stmt.get('type')
        
        if stmt_type == 'assign':
            lhs = stmt['lhs']
            rhs_expr = stmt['rhs']
            rhs_value = self.evaluate_expr(rhs_expr, out_env)
            out_env[lhs] = rhs_value
        
        elif stmt_type == 'assume':
            cond = stmt['cond']
            cond_value = self.evaluate_expr(cond, out_env)
            # 假设条件为真（简化处理）
        
        elif stmt_type == 'phi':
            # Phi函数：合并所有前驱的值
            phi_values = stmt.get('values', [])
            if phi_values:
                result = phi_values[0]
                for v in phi_values[1:]:
                    result = result.join(v)
                out_env[stmt['lhs']] = result
        
        return out_env


def example_simple_constant():
    """简单常量传播"""
    cp = ConstantPropagation()
    
    env = {}
    
    # x = 10
    env = cp.transfer({'type': 'assign', 'lhs': 'x', 'rhs': 10}, env)
    # y = x + 5
    env = cp.transfer({'type': 'assign', 'lhs': 'y', 'rhs': {'op': '+', 'left': 'x', 'right': 5}}, env)
    # z = y + x
    env = cp.transfer({'type': 'assign', 'lhs': 'z', 'rhs': {'op': '+', 'left': 'y', 'right': 'x'}}, env)
    
    print("简单传播结果:")
    for var, val in env.items():
        print(f"  {var} = {val}")


def example_branch_constant():
    """分支常量传播"""
    cp = ConstantPropagation()
    
    # 初始环境
    env = {'x': LatticeValue.constant(5)}
    
    # if (x > 0) then { y = x } else { y = -x }
    # 分支条件 x > 0 为真
    # y = x → y = 5
    # y = -x → y = -5
    # 合并：y = 5 ⊔ -5 = NAC
    
    then_env = dict(env)
    then_env = cp.transfer({'type': 'assign', 'lhs': 'y', 'rhs': 'x'}, then_env)
    
    else_env = dict(env)
    else_env = cp.transfer({'type': 'assign', 'lhs': 'y', 'rhs': {'op': '-', 'left': 0, 'right': 'x'}}, else_env)
    
    # 合并
    merged_y = then_env.get('y', LatticeValue.top()).join(else_env.get('y', LatticeValue.top()))
    
    print("分支常量传播:")
    print(f"  then分支: y = {then_env.get('y')}")
    print(f"  else分支: y = {else_env.get('y')}")
    print(f"  合并后: y = {merged_y}")


def example_dead_code():
    """常量条件下的死代码消除"""
    cp = ConstantPropagation()
    
    env = {'flag': LatticeValue.constant(1)}
    
    # if (flag == 1) then { x = 10 } else { y = 20 }
    # flag == 1 为真 → then分支
    # else分支是死代码
    
    # 但分析器只知道flag是NAC（如果只看到flag==1比较）
    # 需要更复杂的条件传播
    
    print("常量条件下的控制流:")


def example_fold():
    """常量折叠"""
    cp = ConstantPropagation()
    
    # x = (3 + 5) * 2
    env = {}
    result = cp.evaluate_expr({'op': '*', 
                               'left': {'op': '+', 'left': 3, 'right': 5}, 
                               'right': 2}, env)
    
    print(f"常量折叠 (3+5)*2 = {result}")


if __name__ == "__main__":
    print("=" * 50)
    print("常量传播分析 测试")
    print("=" * 50)
    
    example_simple_constant()
    print()
    example_branch_constant()
    print()
    example_fold()
