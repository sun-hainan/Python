# -*- coding: utf-8 -*-
"""
拷贝传播分析（Copy Propagation）
功能：用变量的拷贝源替换变量的使用位置

拷贝语句：x = y（无计算的简单赋值）

分析：
1. 识别拷贝语句
2. 追踪拷贝链
3. 传播替换

作者：Copy Propagation Team
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict


class CopyRelation:
    """拷贝关系 x ← y"""
    def __init__(self, src: str, dst: str):
        self.src = src  # 源
        self.dst = dst  # 目标


class CopyPropagation:
    """
    拷贝传播分析
    """

    def __init__(self):
        self.copies: Dict[str, str] = {}  # var → its copy source

    def add_copy(self, dst: str, src: str):
        """添加拷贝关系 dst = src"""
        self.copies[dst] = src

    def resolve_copy(self, var: str) -> Optional[str]:
        """
        解析拷贝链
        
        例如: x = y, y = z → x的最终源是z
        """
        visited = set()
        current = var
        
        while current in self.copies and current not in visited:
            visited.add(current)
            current = self.copies[current]
        
        if current not in visited:
            return current
        return None  # 循环

    def propagate(self, stmts: List[Dict]) -> List[Dict]:
        """
        执行拷贝传播
        
        简化版本：遍历语句，替换可传播的变量
        """
        result = []
        active_copies = {}  # 当前活跃的拷贝
        
        for stmt in stmts:
            stmt_type = stmt.get('type')
            
            if stmt_type == 'assign':
                lhs = stmt.get('lhs')
                rhs = stmt.get('rhs')
                
                # 传播rhs中的拷贝
                propagated_rhs = self._propagate_expr(rhs, active_copies)
                
                # 如果是简单拷贝（x = y），记录
                if isinstance(propagated_rhs, str) and propagated_rhs.isidentifier():
                    # 检查是否简单拷贝
                    original_rhs = stmt.get('rhs')
                    if isinstance(original_rhs, str):
                        active_copies[lhs] = original_rhs
                
                result.append({'type': 'assign', 'lhs': lhs, 'rhs': propagated_rhs})
            
            elif stmt_type == 'if':
                cond = stmt.get('cond')
                propagated_cond = self._propagate_expr(cond, active_copies)
                result.append({'type': 'if', 'cond': propagated_cond})
            
            elif stmt_type == 'call':
                args = stmt.get('args', [])
                propagated_args = [self._propagate_expr(a, active_copies) for a in args]
                result.append({'type': 'call', 'func': stmt.get('func'), 'args': propagated_args})
        
        return result

    def _propagate_expr(self, expr, active_copies: Dict[str, str]):
        """传播表达式中的拷贝"""
        if isinstance(expr, str) and expr in active_copies:
            return active_copies[expr]
        if isinstance(expr, dict):
            result = dict(expr)
            if 'left' in result:
                result['left'] = self._propagate_expr(result['left'], active_copies)
            if 'right' in result:
                result['right'] = self._propagate_expr(result['right'], active_copies)
            if 'args' in result:
                result['args'] = [self._propagate_expr(a, active_copies) for a in result['args']]
            return result
        return expr


def example_simple_copy():
    """简单拷贝传播"""
    cp = CopyPropagation()
    
    stmts = [
        {'type': 'assign', 'lhs': 'x', 'rhs': 'y'},  # x = y
        {'type': 'assign', 'lhs': 'z', 'rhs': {'op': '+', 'left': 'x', 'right': 1}},  # z = x + 1
    ]
    
    cp.add_copy('x', 'y')
    
    propagated = cp.propagate(stmts)
    
    print("拷贝传播:")
    for stmt in propagated:
        print(f"  {stmt}")


def example_chain():
    """拷贝链"""
    cp = CopyPropagation()
    
    stmts = [
        {'type': 'assign', 'lhs': 'a', 'rhs': 'b'},  # a = b
        {'type': 'assign', 'lhs': 'c', 'rhs': 'a'},  # c = a
        {'type': 'assign', 'lhs': 'd', 'rhs': {'op': '*', 'left': 'c', 'right': 2}},  # d = c * 2
    ]
    
    cp.add_copy('a', 'b')
    cp.add_copy('c', 'a')
    
    propagated = cp.propagate(stmts)
    
    print("拷贝链传播:")
    for stmt in propagated:
        print(f"  {stmt}")


def example_resolve():
    """解析拷贝链"""
    cp = CopyPropagation()
    
    cp.add_copy('x', 'y')
    cp.add_copy('y', 'z')
    cp.add_copy('z', 'w')
    
    result = cp.resolve_copy('x')
    print(f"x的最终源: {result}")


if __name__ == "__main__":
    print("=" * 50)
    print("拷贝传播分析 测试")
    print("=" * 50)
    
    example_simple_copy()
    print()
    example_chain()
    print()
    example_resolve()
