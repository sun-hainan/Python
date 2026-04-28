# -*- coding: utf-8 -*-
"""
到达定义分析（Reaching Definitions）
功能：确定变量的定义是否能到达程序点

定义：给变量赋值的语句
到达：当某定义的路径上没有重定义该变量

应用：
1. 常量传播
2. 死代码消除
3. 变量别名分析

数据流分析：
- 方向：前向
- 格：幂集（定义的集合）
- Meet：∪（并集）
- Transfer: OUT[B] = gen(B) ∪ (IN[B] - kill(B))

作者：Reaching Definitions Team
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict, deque


class ReachingDefinitions:
    """
    到达定义分析
    """

    def __init__(self):
        self.gen: Dict[str, Set[int]] = {}  # block → 生成的定义
        self.kill: Dict[str, Set[int]] = {}  # block → 杀死的定义
        self.in_defs: Dict[str, Set[int]] = {}  # block → 入口定义
        self.out_defs: Dict[str, Set[int]] = {}  # block → 出口定义

    def compute_gen_kill(self, stmts: List[Dict], block_id: str, all_defs: Dict[str, List[int]]):
        """
        计算gen和kill集合
        
        gen(B): B中生成的定义
        kill(B): B中杀死的其他定义
        """
        gen_set: Set[int] = set()
        kill_set: Set[int] = set()
        defined_vars: Set[str] = set()
        
        for stmt in stmts:
            if stmt.get('type') == 'assign':
                lhs = stmt.get('lhs')
                if lhs:
                    # 这是对lhs的定义
                    if lhs not in defined_vars:
                        # 新定义
                        if lhs in all_defs:
                            for def_id in all_defs[lhs]:
                                kill_set.add(def_id)
                    defined_vars.add(lhs)
                    gen_set.add(self._get_def_id(block_id, lhs, stmts.index(stmt)))
        
        self.gen[block_id] = gen_set
        self.kill[block_id] = kill_set

    def _get_def_id(self, block_id: str, var: str, stmt_index: int) -> int:
        """生成定义ID"""
        return hash((block_id, var, stmt_index)) % 1000000

    def analyze(self, cfg: 'CFG') -> Dict[str, Set[int]]:
        """
        执行到达定义分析
        
        Returns:
            每个块的IN定义集合
        """
        # 初始化
        for block in cfg.blocks:
            self.in_defs[block.id] = set()
            self.out_defs[block.id] = self.gen.get(block.id, set())
        
        # 迭代直到不动点
        changed = True
        while changed:
            changed = False
            
            for block in cfg.blocks:
                # IN[B] = ∪ OUT[P] for all P in pred(B)
                in_set = set()
                for pred in block.preds:
                    in_set |= self.out_defs.get(pred.id, set())
                
                if in_set != self.in_defs.get(block.id, set()):
                    self.in_defs[block.id] = in_set
                    changed = True
                
                # OUT[B] = gen(B) ∪ (IN[B] - kill(B))
                kill_set = self.kill.get(block.id, set())
                new_out = self.gen.get(block.id, set()) | (in_set - kill_set)
                
                if new_out != self.out_defs.get(block.id, set()):
                    self.out_defs[block.id] = new_out
                    changed = True
        
        return self.in_defs

    def may_reach(self, block_id: str, def_id: int) -> bool:
        """检查定义是否可能到达块"""
        return def_id in self.in_defs.get(block_id, set())


class CFG:
    """简化CFG"""
    def __init__(self):
        self.blocks: List = []


def example_simple():
    """简单示例"""
    rd = ReachingDefinitions()
    
    # 模拟基本块
    class Block:
        def __init__(self, bid, stmts, preds=None, succs=None):
            self.id = bid
            self.stmts = stmts
            self.preds = preds or []
            self.succs = succs or []
    
    b1 = Block(1, [{'type': 'assign', 'lhs': 'x', 'rhs': 10}])
    b2 = Block(2, [{'type': 'assign', 'lhs': 'y', 'rhs': 'x'}])
    b3 = Block(3, [{'type': 'assign', 'lhs': 'x', 'rhs': 20}])
    
    b1.succs = [b2]
    b2.preds = [b1]
    b2.succs = [b3]
    b3.preds = [b2]
    
    cfg = CFG()
    cfg.blocks = [b1, b2, b3]
    
    rd.compute_gen_kill(b1.stmts, '1', {})
    rd.compute_gen_kill(b2.stmts, '2', {})
    rd.compute_gen_kill(b3.stmts, '3', {})
    
    rd.analyze(cfg)
    
    print("到达定义:")
    for block in cfg.blocks:
        print(f"  Block{block.id}: IN={len(rd.in_defs.get(block.id, set()))} defs")


def example_with_loop():
    """带循环的示例"""
    rd = ReachingDefinitions()
    
    print("循环中的到达定义:")


if __name__ == "__main__":
    print("=" * 50)
    print("到达定义分析 测试")
    print("=" * 50)
    
    example_simple()
    print()
    example_with_loop()
