# -*- coding: utf-8 -*-
"""
非常忙表达式分析（Very Busy Expressions）
功能：找出在程序点之后必定会被使用的表达式

非常忙表达式：在某点之后，所有执行路径都会计算的表达式

用途：
1. 表达式提升（移动到公共前缀）
2. 代码移动优化

数据流分析：
- 方向：后向
- 格：幂集
- Meet：∩（交集）
- Transfer: IN[B] = use(B) ∪ (OUT[B] - kill(B))

作者：Very Busy Expressions Team
"""

from typing import List, Dict, Set, Tuple
from collections import defaultdict


class VeryBusyExpressions:
    """
    非常忙表达式分析
    """

    def __init__(self):
        self.vb_in: Dict[str, Set[str]] = {}
        self.vb_out: Dict[str, Set[str]] = {}

    def compute_use_kill(self, stmts: List[Dict]) -> Tuple[Set[str], Set[str]]:
        """
        计算use和kill集合
        
        use(B): B中使用的表达式
        kill(B): B中重新定义的变量涉及的表达式
        """
        use_set: Set[str] = set()
        kill_set: Set[str] = set()
        
        for stmt in stmts:
            if stmt.get('type') == 'assign':
                rhs = stmt.get('rhs')
                lhs = stmt.get('lhs')
                
                # 收集rhs中的表达式
                expr = self._expr_to_str(rhs)
                if expr:
                    use_set.add(expr)
                
                # lhs重定义会kill使用该变量的表达式
                if lhs:
                    kill_set.add(lhs)
        
        return use_set, kill_set

    def _expr_to_str(self, expr) -> str:
        """表达式转字符串"""
        if isinstance(expr, dict):
            op = expr.get('op', '')
            args = expr.get('args', [])
            if args:
                left = self._expr_to_str(args[0]) if len(args) > 0 else ''
                right = self._expr_to_str(args[1]) if len(args) > 1 else ''
                return f"({left}{op}{right})"
        return ""

    def analyze(self, cfg: 'CFG') -> Dict[str, Set[str]]:
        """
        执行非常忙表达式分析
        
        Returns:
            每个块的IN集合
        """
        # 初始化
        for block in cfg.blocks:
            self.vb_in[block.id] = set()
            self.vb_out[block.id] = set()
        
        changed = True
        while changed:
            changed = False
            
            for block in cfg.blocks:
                # OUT[B] = ∩ IN[S] for all S in succ(B)
                out_set = set()
                if block.succs:
                    for succ in block.succs:
                        out_set |= self.vb_in.get(succ.id, set())
                    self.vb_out[block.id] = out_set
                else:
                    # 无后继：OUT = ∅
                    self.vb_out[block.id] = set()
                
                # IN[B] = use(B) ∪ (OUT[B] - kill(B))
                use_set, kill_set = self.compute_use_kill(block.stmts)
                new_in = use_set | (self.vb_out[block.id] - kill_set)
                
                if new_in != self.vb_in.get(block.id, set()):
                    self.vb_in[block.id] = new_in
                    changed = True
        
        return self.vb_in


class CFG:
    """简化CFG"""
    def __init__(self):
        self.blocks: List = []


def example():
    """示例"""
    analyzer = VeryBusyExpressions()
    
    print("非常忙表达式分析:")


if __name__ == "__main__":
    print("=" * 50)
    print("非常忙表达式分析 测试")
    print("=" * 50)
    
    example()
