# -*- coding: utf-8 -*-
"""
死代码检测（Dead Code Detection）
功能：识别程序中永远不会被执行的代码

死代码类型：
1. 不可达代码：控制流不可达
2. 死变量：赋值后从不使用
3. 冗余计算：结果不使用

作者：Dead Code Detection Team
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict


class DeadCodeDetector:
    """
    死代码检测器
    
    使用活跃变量分析和控制流分析
    """

    def __init__(self):
        self.reachable: Set[int] = set()  # 可达语句
        self.dead_stmts: List[int] = []  # 死语句
        self.live_vars: Dict[int, Set[str]] = {}  # 每点的活跃变量

    def detect_unreachable(self, cfg: 'CFG') -> Set[int]:
        """
        检测不可达代码
        
        使用可达性分析
        """
        reachable = {cfg.entry}
        worklist = deque([cfg.entry])
        
        while worklist:
            current = worklist.popleft()
            for succ in current.succs:
                if succ not in reachable:
                    reachable.add(succ)
                    worklist.append(succ)
        
        self.reachable = reachable
        return reachable

    def detect_dead_assignments(self, stmts: List[Dict], 
                               live_vars: Dict[int, Set[str]]) -> List[int]:
        """
        检测死赋值语句
        
        如果赋值语句的左端变量在后续都不活跃，则为死代码
        """
        dead = []
        
        for i, stmt in enumerate(stmts):
            if stmt.get('type') == 'assign':
                lhs = stmt.get('lhs')
                if lhs:
                    # 检查后续是否活跃
                    is_live = False
                    for j in range(i + 1, len(stmts)):
                        if lhs in live_vars.get(j, set()):
                            is_live = True
                            break
                    
                    if not is_live:
                        dead.append(i)
        
        self.dead_stmts = dead
        return dead

    def detect_dead_branches(self, cfg: 'CFG') -> List[Tuple[int, str]]:
        """
        检测死分支
        
        如果条件恒为真/假，则一个分支永远不执行
        """
        dead_branches = []
        
        for block in cfg.blocks:
            if block.stmts and block.stmts[-1].get('type') == 'if':
                cond = block.stmts[-1].get('cond')
                # 简化：假设条件不恒定
                pass
        
        return dead_branches


class CFG:
    """简化CFG"""
    def __init__(self):
        self.blocks: List = []
        self.entry = None


def example_unreachable():
    """不可达代码检测"""
    detector = DeadCodeDetector()
    
    # 简化CFG
    cfg = CFG()
    
    # 模拟块
    class Block:
        def __init__(self, bid, succs):
            self.id = bid
            self.succs = succs
    
    b0 = Block(0, [1])
    b1 = Block(1, [2, 3])
    b2 = Block(2, [4])
    b3 = Block(3, [4])  # 死代码块
    b4 = Block(4, [])
    
    cfg.blocks = [b0, b1, b2, b3, b4]
    cfg.entry = b0
    
    reachable = detector.detect_unreachable(cfg)
    print(f"可达块: {sorted(b.id for b in reachable)}")
    print(f"不可达块: {sorted(b.id for b in cfg.blocks if b not in reachable)}")


def example_dead_assignment():
    """死赋值检测"""
    detector = DeadCodeDetector()
    
    stmts = [
        {'type': 'assign', 'lhs': 'x', 'rhs': 10},
        {'type': 'assign', 'lhs': 'y', 'rhs': 20},  # 可能是死代码
        {'type': 'assign', 'lhs': 'z', 'rhs': {'op': '+', 'left': 'x', 'right': 1}},
        {'type': 'output', 'value': 'z'},
    ]
    
    # 假设活跃变量
    live_vars = {
        0: set(),
        1: {'x', 'z'},
        2: {'z'},
        3: set(),
    }
    
    dead = detector.detect_dead_assignments(stmts, live_vars)
    print(f"死赋值语句索引: {dead}")
    for i in dead:
        print(f"  语句{i}: {stmts[i]}")


def example_constant_folding_dead():
    """常量折叠后的死代码"""
    detector = DeadCodeDetector()
    
    stmts = [
        {'type': 'assign', 'lhs': 'x', 'rhs': 10},
        {'type': 'assign', 'lhs': 'y', 'rhs': 20},
        {'type': 'assign', 'lhs': 'z', 'rhs': {'op': '-', 'left': 'y', 'right': 'y'}},  # 恒为0
        {'type': 'assign', 'lhs': 'w', 'rhs': 'z'},  # z被使用
    ]
    
    # 活跃变量分析
    live_vars = {
        0: {'x'},
        1: {'x', 'y'},
        2: {'x', 'y', 'z'},
        3: {'x', 'y', 'z', 'w'},
    }
    
    dead = detector.detect_dead_assignments(stmts, live_vars)
    print(f"检测到的死代码: {dead}")


if __name__ == "__main__":
    print("=" * 50)
    print("死代码检测 测试")
    print("=" * 50)
    
    example_unreachable()
    print()
    example_dead_assignment()
    print()
    example_constant_folding_dead()
