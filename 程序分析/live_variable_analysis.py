# -*- coding: utf-8 -*-
"""
活跃变量分析（Live Variable Analysis）
功能：确定变量在程序点是否活跃（后续还会被使用）

用途：
1. 寄存器分配
2. 死代码消除
3. 释放堆对象

数据流分析：
- 方向：后向
- 格：P(Variables) - 变量的幂集
- Transfer: OUT[B] = ⋃ IN[succ] for succ in succs(B)
           IN[B] = use(B) ∪ (OUT[B] - def(B))

作者：Live Variable Analysis Team
"""

from typing import List, Dict, Set, Tuple
from collections import defaultdict


class LiveVariableAnalysis:
    """
    活跃变量分析
    
    后向数据流分析
    """

    def __init__(self):
        # use[B]: B中引用（使用）但在B之前未定义的变量
        # def[B]: B中定义（赋值）但在B中后续未重新定义的变量
        self.use: Dict[str, Set[str]] = defaultdict(set)
        self.defs: Dict[str, Set[str]] = defaultdict(set)
        self.live_in: Dict[str, Set[str]] = {}
        self.live_out: Dict[str, Set[str]] = {}

    def compute_use_def(self, stmts: List[Dict], block_id: str):
        """
        计算基本块的use和def集合
        
        use(B): 在B中引用但在B中任何定义之前的变量
        def(B): 在B中定义的变量集合
        """
        defined: Set[str] = set()
        use_set: Set[str] = set()
        
        for stmt in reversed(stmts):
            stmt_type = stmt.get('type')
            
            if stmt_type == 'assign':
                lhs = stmt.get('lhs')
                rhs = stmt.get('rhs')
                
                # 检查rhs中使用的变量
                used_vars = self._extract_vars(rhs)
                for v in used_vars:
                    if v not in defined:
                        use_set.add(v)
                
                # lhs的定义（在后续分析中生效）
                if lhs:
                    defined.add(lhs)
            
            elif stmt_type == 'if':
                cond = stmt.get('cond')
                used_vars = self._extract_vars(cond)
                for v in used_vars:
                    if v not in defined:
                        use_set.add(v)
            
            elif stmt_type == 'call':
                # 函数调用可能有副作用
                pass
        
        self.use[block_id] = use_set
        self.defs[block_id] = defined

    def _extract_vars(self, expr) -> Set[str]:
        """提取表达式中的变量"""
        if isinstance(expr, str) and expr.isidentifier():
            return {expr}
        if isinstance(expr, dict):
            result = set()
            for key, val in expr.items():
                if key in ('left', 'right', 'arg', 'args'):
                    result |= self._extract_vars(val)
            return result
        if isinstance(expr, (list, tuple)):
            result = set()
            for item in expr:
                result |= self._extract_vars(item)
            return result
        return set()

    def analyze(self, cfg: 'CFG', entry_block: str) -> Dict[str, Set[str]]:
        """
        执行活跃变量分析
        
        Args:
            cfg: 控制流图
            entry_block: 入口块ID
            
        Returns:
            每个块的live_in集合
        """
        # 初始化
        for block in cfg.blocks:
            self.live_in[block.id] = set()
            self.live_out[block.id] = set()
        
        # 迭代直到不动点
        changed = True
        while changed:
            changed = False
            
            for block in reversed(cfg.blocks):
                # OUT[B] = ⋃ IN[succ] for all succ
                out_set = set()
                for succ in block.succs:
                    out_set |= self.live_in.get(succ.id, set())
                
                if out_set != self.live_out.get(block.id, set()):
                    self.live_out[block.id] = out_set
                    changed = True
                
                # IN[B] = use(B) ∪ (OUT[B] - def(B))
                def_set = self.defs.get(block.id, set())
                new_in = self.use.get(block.id, set()) | (out_set - def_set)
                
                if new_in != self.live_in.get(block.id, set()):
                    self.live_in[block.id] = new_in
                    changed = True
        
        return self.live_in

    def get_live_at_point(self, block_id: str) -> Set[str]:
        """获取块入口处的活跃变量"""
        return self.live_in.get(block_id, set())


class CFG:
    """简化CFG"""
    def __init__(self):
        self.blocks: List['Block'] = []


class Block:
    """简化基本块"""
    def __init__(self, bid: str):
        self.id = bid
        self.stmts: List = []
        self.preds: List['Block'] = []
        self.succs: List['Block'] = []


def example_simple():
    """简单示例"""
    # x = 10
    # y = x + 1
    # z = y + 2
    # w = z + 3
    # return w
    
    analyzer = LiveVariableAnalysis()
    
    stmts = [
        {'type': 'assign', 'lhs': 'x', 'rhs': 10},
        {'type': 'assign', 'lhs': 'y', 'rhs': {'op': '+', 'left': 'x', 'right': 1}},
        {'type': 'assign', 'lhs': 'z', 'rhs': {'op': '+', 'left': 'y', 'right': 2}},
        {'type': 'assign', 'lhs': 'w', 'rhs': {'op': '+', 'left': 'z', 'right': 3}},
    ]
    
    # 创建模拟CFG
    cfg = CFG()
    blocks = [Block(str(i)) for i in range(5)]
    for b in blocks[:-1]:
        b.succs.append(blocks[blocks.index(b) + 1])
    cfg.blocks = blocks
    
    # 计算use/def
    for i, block in enumerate(cfg.blocks):
        if i < len(stmts):
            analyzer.compute_use_def([stmts[i]], block.id)
    
    # 分析
    analyzer.analyze(cfg, '0')
    
    print("活跃变量分析:")
    for block in cfg.blocks:
        live_in = analyzer.live_in.get(block.id, set())
        print(f"  块{block.id}入口: {live_in if live_in else '∅'}")


def example_dead_code():
    """死代码消除示例"""
    analyzer = LiveVariableAnalysis()
    
    # a = 10        # a已定义但之后不再使用 → 死代码
    # b = 20
    # c = a + b     # 这里之后a不再使用
    # d = b + c
    
    stmts = [
        {'type': 'assign', 'lhs': 'a', 'rhs': 10},
        {'type': 'assign', 'lhs': 'b', 'rhs': 20},
        {'type': 'assign', 'lhs': 'c', 'rhs': {'op': '+', 'left': 'a', 'right': 'b'}},
        {'type': 'assign', 'lhs': 'd', 'rhs': {'op': '+', 'left': 'b', 'right': 'c'}},
    ]
    
    cfg = CFG()
    blocks = [Block(str(i)) for i in range(len(stmts))]
    for b in blocks[:-1]:
        b.succs.append(blocks[blocks.index(b) + 1])
    cfg.blocks = blocks
    
    for i, block in enumerate(cfg.blocks):
        analyzer.compute_use_def([stmts[i]], block.id)
    
    analyzer.analyze(cfg, '0')
    
    print("活跃变量分析（判断死代码）:")
    for i, stmt in enumerate(stmts):
        live_vars = analyzer.live_in.get(str(i), set())
        lhs = stmt.get('lhs')
        if lhs and lhs not in live_vars:
            print(f"  语句 {stmt}: {lhs} 不是活跃 → 可能是死代码")


def example_branch():
    """分支活跃变量"""
    analyzer = LiveVariableAnalysis()
    
    # x = input()
    # if (x > 0) {
    #   y = x        # y只在then分支使用
    # } else {
    #   z = x        # z只在else分支使用
    # }
    # w = y + z      # y和z都需要
    
    stmts_if = [
        {'type': 'assign', 'lhs': 'y', 'rhs': 'x'},
    ]
    stmts_else = [
        {'type': 'assign', 'lhs': 'z', 'rhs': 'x'},
    ]
    
    analyzer.compute_use_def(stmts_if, 'then')
    analyzer.compute_use_def(stmts_else, 'else')
    
    print("分支活跃变量:")
    print(f"  then分支: use={analyzer.use.get('then', set())}, def={analyzer.defs.get('then', set())}")
    print(f"  else分支: use={analyzer.use.get('else', set())}, def={analyzer.defs.get('else', set())}")


if __name__ == "__main__":
    print("=" * 50)
    print("活跃变量分析 测试")
    print("=" * 50)
    
    example_simple()
    print()
    example_dead_code()
    print()
    example_branch()
