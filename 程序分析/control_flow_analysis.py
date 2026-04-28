# -*- coding: utf-8 -*-
"""
控制流分析（Control Flow Analysis）
功能：构建程序的控制流图(CFG)，分析程序结构

控制流图：
- 节点：基本块（无跳转的语句序列）
- 边：控制流转移

分析类型：
1. 基本块划分
2. 支配关系（Dominance）
3. 循环检测
4. 自然循环识别

作者：Control Flow Analysis Team
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict, deque


class BasicBlock:
    """基本块"""
    def __init__(self, block_id: int):
        self.id = block_id
        self.stmts: List = []  # 块内语句
        self.preds: List['BasicBlock'] = []  # 前驱
        self.succs: List['BasicBlock'] = []  # 后继

    def add_stmt(self, stmt):
        self.stmts.append(stmt)

    def is_empty(self) -> bool:
        return len(self.stmts) == 0

    def __repr__(self):
        return f"B{self.id}"


class CFG:
    """控制流图"""
    def __init__(self, entry: BasicBlock = None, exit: BasicBlock = None):
        self.entry = entry
        self.exit = exit
        self.blocks: List[BasicBlock] = []

    def add_block(self, block: BasicBlock):
        self.blocks.append(block)

    def get_preds(self, block: BasicBlock) -> List['BasicBlock']:
        return block.preds

    def get_succs(self, block: BasicBlock) -> List['BasicBlock']:
        return block.succs


class ControlFlowAnalyzer:
    """
    控制流分析器
    
    功能：
    1. 构建基本块
    2. 识别循环
    3. 计算支配关系
    """

    def __init__(self):
        self.cfg: CFG = None
        self.blocks: List[BasicBlock] = []
        self.next_block_id = 0

    def build_cfg(self, stmts: List[Dict]) -> CFG:
        """
        构建控制流图
        
        Args:
            stmts: 语句列表
            
        Returns:
            CFG对象
        """
        # 划分基本块
        self.blocks = self._partition_blocks(stmts)
        
        # 连接块
        for i, block in enumerate(self.blocks):
            if i < len(self.blocks) - 1:
                block.succs.append(self.blocks[i + 1])
        
        # 处理跳转语句
        self._process_jumps()
        
        # 创建CFG
        cfg = CFG(entry=self.blocks[0] if self.blocks else None,
                  exit=self.blocks[-1] if self.blocks else None)
        cfg.blocks = self.blocks
        
        self.cfg = cfg
        return cfg

    def _partition_blocks(self, stmts: List[Dict]) -> List[BasicBlock]:
        """划分基本块"""
        blocks = []
        current_block = BasicBlock(self.next_block_id)
        self.next_block_id += 1
        
        leaders = {0}  # 块的起始位置
        
        for i, stmt in enumerate(stmts):
            if stmt.get('type') in ('if', 'while', 'goto', 'return'):
                leaders.add(i)
                if i + 1 < len(stmts):
                    leaders.add(i + 1)
        
        for i, stmt in enumerate(stmts):
            if i in leaders and not current_block.is_empty():
                blocks.append(current_block)
                current_block = BasicBlock(self.next_block_id)
                self.next_block_id += 1
            
            current_block.add_stmt(stmt)
        
        if not current_block.is_empty():
            blocks.append(current_block)
        
        return blocks

    def _process_jumps(self):
        """处理跳转语句"""
        for block in self.blocks:
            if not block.stmts:
                continue
            last_stmt = block.stmts[-1]
            stmt_type = last_stmt.get('type')
            
            if stmt_type == 'goto':
                target = last_stmt.get('target')
                # 找到目标块并连接
                for tb in self.blocks:
                    if tb.id == target:
                        block.succs.append(tb)
                        tb.preds.append(block)
            
            elif stmt_type == 'if':
                then_target = last_stmt.get('then')
                else_target = last_stmt.get('else')
                
                for tb in self.blocks:
                    if tb.id == then_target:
                        block.succs.append(tb)
                        tb.preds.append(block)
                    if tb.id == else_target:
                        block.succs.append(tb)
                        tb.preds.append(block)

    def find_dominators(self) -> Dict[int, Set[int]]:
        """
        计算支配关系
        
        dom(n) = {n} ∪ (∩ dom(p) for all p in preds(n))
        """
        if not self.blocks:
            return {}
        
        n = len(self.blocks)
        id_to_idx = {b.id: i for i, b in enumerate(self.blocks)}
        idx_to_id = {i: b.id for i, b in enumerate(self.blocks)}
        
        # 初始化
        doms: List[Set[int]] = [set(range(n)) for _ in range(n)]
        doms[0] = {0}  # 入口节点只支配自己
        
        changed = True
        while changed:
            changed = False
            for i, block in enumerate(self.blocks):
                if i == 0:
                    continue
                
                new_dom = set()
                if block.preds:
                    first_pred_idx = id_to_idx[block.preds[0].id]
                    new_dom = set(doms[first_pred_idx])
                    for pred in block.preds[1:]:
                        pred_idx = id_to_idx[pred.id]
                        new_dom &= doms[pred_idx]
                
                new_dom.add(i)
                
                if new_dom != doms[i]:
                    doms[i] = new_dom
                    changed = True
        
        # 转换为block id
        result = {}
        for i, dom_set in enumerate(doms):
            result[idx_to_id[i]] = {idx_to_id[idx] for idx in dom_set}
        
        return result

    def find_loops(self) -> List[Dict]:
        """
        识别自然循环
        
        Returns:
            循环列表，每个循环包含 {header, body, back_edges}
        """
        loops = []
        doms = self.find_dominators()
        
        for block in self.blocks:
            for succ in block.succs:
                # 如果block支配 succ，则 (block, succ) 是回边
                if succ.id in doms.get(block.id, set()):
                    # 找到了自然循环
                    loop = {
                        'header': succ,
                        'back_edge': (block, succ),
                        'body': self._get_loop_body(succ, block)
                    }
                    loops.append(loop)
        
        return loops

    def _get_loop_body(self, header: BasicBlock, back_src: BasicBlock) -> Set[BasicBlock]:
        """获取循环体中的所有节点"""
        body = {header}
        worklist = deque([back_src])
        
        while worklist:
            current = worklist.popleft()
            if current not in body:
                body.add(current)
                for pred in current.preds:
                    if pred not in body:
                        worklist.append(pred)
        
        return body


def example_cfg_build():
    """CFG构建示例"""
    analyzer = ControlFlowAnalyzer()
    
    stmts = [
        {'type': 'assign', 'var': 'x', 'val': 0},
        {'type': 'assign', 'var': 'sum', 'val': 0},
        {'type': 'while', 'cond': 'x < 10', 'body': 5, 'end': 8},
        {'type': 'assign', 'var': 'sum', 'expr': {'op': '+', 'left': 'sum', 'right': 'x'}},
        {'type': 'assign', 'var': 'x', 'expr': {'op': '+', 'left': 'x', 'right': 1}},
        {'type': 'goto', 'target': 2},
        {'type': 'return', 'val': 'sum'},
    ]
    
    cfg = analyzer.build_cfg(stmts)
    
    print("控制流图:")
    print(f"  基本块数: {len(cfg.blocks)}")
    print(f"  入口块: {cfg.entry}")
    print(f"  出口块: {cfg.exit}")
    
    for block in cfg.blocks:
        print(f"\n  Block {block.id}:")
        for stmt in block.stmts[:3]:
            print(f"    {stmt}")


def example_dominators():
    """支配关系示例"""
    analyzer = ControlFlowAnalyzer()
    
    # 简单线性代码
    stmts = [
        {'type': 'assign', 'var': 'x', 'val': 1},
        {'type': 'assign', 'var': 'y', 'val': 2},
        {'type': 'assign', 'var': 'z', 'val': 3},
        {'type': 'return', 'val': 'z'},
    ]
    
    cfg = analyzer.build_cfg(stmts)
    doms = analyzer.find_dominators()
    
    print("支配关系:")
    for block_id, dom_set in doms.items():
        print(f"  B{block_id} 支配: {dom_set}")


def example_loop_detection():
    """循环检测示例"""
    analyzer = ControlFlowAnalyzer()
    
    # while循环
    stmts = [
        {'type': 'assign', 'var': 'i', 'val': 0},
        {'type': 'while', 'cond': 'i < 10'},
        {'type': 'assign', 'var': 'i', 'expr': {'op': '+', 'left': 'i', 'right': 1}},
        {'type': 'return', 'val': 'i'},
    ]
    
    cfg = analyzer.build_cfg(stmts)
    loops = analyzer.find_loops()
    
    print(f"检测到 {len(loops)} 个循环")
    for loop in loops:
        print(f"  循环头: {loop['header']}")
        print(f"  循环体: {loop['body']}")


if __name__ == "__main__":
    print("=" * 50)
    print("控制流分析 测试")
    print("=" * 50)
    
    example_cfg_build()
    print()
    example_dominators()
    print()
    example_loop_detection()
