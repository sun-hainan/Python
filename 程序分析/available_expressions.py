# -*- coding: utf-8 -*-
"""
可用表达式分析（Available Expressions Analysis）
功能：找出在程序点必定已计算的表达式

可用表达式：在某点之前，所有路径都会计算的表达式

应用：
1. 公共子表达式消除（CSE）
2. 死代码消除
3. 复制传播

数据流分析：
- 方向：前向
- 格：幂集（表达式的集合）
- Meet：∩（交集）
- Transfer: OUT[B] = gen(B) ∪ (IN[B] - kill(B))

作者：Available Expressions Team
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict


class AvailableExpressions:
    """
    可用表达式分析
    """

    def __init__(self):
        self.avail_in: Dict[str, Set[str]] = {}
        self.avail_out: Dict[str, Set[str]] = {}

    def compute_gen_kill(self, stmts: List[Dict]) -> Tuple[Set[str], Set[str]]:
        """
        计算gen和kill集合
        
        gen(B): B中产生的表达式
        kill(B): B中杀死的表达式（重定义的变量）
        """
        gen_set: Set[str] = set()
        kill_set: Set[str] = set()
        
        for stmt in stmts:
            if stmt.get('type') == 'assign':
                lhs = stmt.get('lhs')
                rhs = stmt.get('rhs')
                
                if isinstance(rhs, dict):
                    expr_str = self._expr_to_str(rhs)
                    if lhs in kill_set:
                        gen_set.discard(expr_str)
                    else:
                        gen_set.add(expr_str)
                    kill_set.add(lhs)
        
        return gen_set, kill_set

    def _expr_to_str(self, expr: Dict) -> str:
        """表达式转字符串（用于唯一标识）"""
        if isinstance(expr, dict):
            op = expr.get('op', '')
            args = expr.get('args', [])
            if args:
                left = self._expr_to_str(args[0]) if len(args) > 0 else ''
                right = self._expr_to_str(args[1]) if len(args) > 1 else ''
                return f"({left}{op}{right})"
        return str(expr)

    def analyze(self, cfg: 'CFG') -> Dict[str, Set[str]]:
        """
        执行可用表达式分析
        
        Returns:
            每个块的可用表达式IN集合
        """
        # 初始化所有块
        for block in cfg.blocks:
            self.avail_in[block.id] = set()
            self.avail_out[block.id] = set()
        
        # 入口块：IN = ∅
        if cfg.entry:
            self.avail_in[cfg.entry.id] = set()
        
        changed = True
        while changed:
            changed = False
            
            for block in cfg.blocks:
                # IN[B] = ∩ OUT[P] for all P in pred(B)
                if block.preds:
                    in_set = None
                    for pred in block.preds:
                        pred_out = self.avail_out.get(pred.id, set())
                        if in_set is None:
                            in_set = set(pred_out)
                        else:
                            in_set &= pred_out
                    self.avail_in[block.id] = in_set or set()
                
                # 计算gen/kill
                gen_set, kill_set = self.compute_gen_kill(block.stmts)
                
                # OUT[B] = gen(B) ∪ (IN[B] - kill(B))
                new_out = gen_set | (self.avail_in[block.id] - kill_set)
                
                if new_out != self.avail_out.get(block.id, set()):
                    self.avail_out[block.id] = new_out
                    changed = True
        
        return self.avail_in


class CFG:
    """简化CFG"""
    def __init__(self):
        self.blocks: List = []


def example_common_subexpr():
    """公共子表达式消除示例"""
    analyzer = AvailableExpressions()
    
    # 模拟基本块
    stmts = [
        {'type': 'assign', 'lhs': 'a', 'rhs': {'op': '+', 'args': ['x', 'y']}},
        {'type': 'assign', 'lhs': 'b', 'rhs': {'op': '+', 'args': ['x', 'y']}},  # CSE候选
        {'type': 'assign', 'lhs': 'c', 'rhs': {'op': '*', 'args': ['a', 'b']}},
    ]
    
    gen_set, kill_set = analyzer.compute_gen_kill(stmts)
    
    print(f"Gen: {gen_set}")
    print(f"Kill: {kill_set}")


def example_cfg_analysis():
    """CFG分析示例"""
    analyzer = AvailableExpressions()
    
    # 简单CFG
    cfg = CFG()
    
    class Block:
        def __init__(self, bid, stmts, preds=None, succs=None):
            self.id = bid
            self.stmts = stmts
            self.preds = preds or []
            self.succs = succs or []
    
    b1 = Block(1, [{'type': 'assign', 'lhs': 'x', 'rhs': {'op': '+', 'args': ['a', 'b']}}])
    b2 = Block(2, [{'type': 'assign', 'lhs': 'y', 'rhs': {'op': '*', 'args': ['x', 'c']}}])
    
    b1.succs = [b2]
    b2.preds = [b1]
    
    cfg.blocks = [b1, b2]
    cfg.entry = b1
    
    analyzer.analyze(cfg)
    
    print("可用表达式:")
    for block in cfg.blocks:
        print(f"  Block{block.id}: IN={analyzer.avail_in.get(block.id, set())}")


if __name__ == "__main__":
    print("=" * 50)
    print("可用表达式分析 测试")
    print("=" * 50)
    
    example_common_subexpr()
    print()
    example_cfg_analysis()
