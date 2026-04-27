# -*- coding: utf-8 -*-
"""
算法实现：编译器优化 / dead_code_elimination

本文件实现 dead_code_elimination 相关的算法功能。
"""

from typing import List, Set, Dict, Tuple, Optional
from collections import defaultdict


class DeadCodeEliminator:
    """
    死代码消除器
    使用数据流分析移除:
    1. 不可达代码
    2. 无用赋值(写但从不读取)
    3. 总是假的条件跳转
    """
    
    def __init__(self):
        self.cfg = {}  # 控制流图 {block_id: successors}
        self.stmts = {}  # 语句 {block_id: [statements]}
        self.def_use = {}  # 定义-使用链 {var: [(block, stmt_idx)]}
    
    def add_block(self, block_id: int, stmts: List):
        """添加基本块"""
        self.cfg[block_id] = set()
        self.stmts[block_id] = stmts
    
    def add_edge(self, from_id: int, to_id: int):
        """添加控制流边"""
        self.cfg[from_id].add(to_id)
    
    def find_unreachable_blocks(self, entry: int) -> Set[int]:
        """
        找出不可达块
        
        Args:
            entry: 入口块ID
        
        Returns:
            不可达块集合
        """
        reachable = {entry}
        worklist = [entry]
        
        while worklist:
            block = worklist.pop()
            for succ in self.cfg.get(block, []):
                if succ not in reachable:
                    reachable.add(succ)
                    worklist.append(succ)
        
        all_blocks = set(self.cfg.keys())
        return all_blocks - reachable
    
    def compute_reaching_definitions(self) -> Dict[Tuple[int, int], Set[str]]:
        """
        计算 Reaching Definitions
        对于每个块入口,哪些定义可以到达
        
        Returns:
            {(block_id, stmt_idx): set of defined vars}
        """
        # GEN-KILL形式
        gen = {}  # {(block, stmt_idx): vars defined}
        kill = {}  # {(block, stmt_idx): vars killed}
        
        for block_id, stmts in self.stmts.items():
            killed = set()
            for idx, stmt in enumerate(stmts):
                gen[(block_id, idx)] = set()
                kill[(block_id, idx)] = set()
                
                # 如果是赋值语句
                if hasattr(stmt, 'lhs'):
                    var = stmt.lhs
                    
                    # GEN:这个语句定义了var
                    gen[(block_id, idx)].add(var)
                    
                    # KILL:之前所有定义var的语句被杀死
                    for prev_idx in range(idx):
                        if (block_id, prev_idx) in gen and var in gen[(block_id, prev_idx)]:
                            kill[(block_id, idx)].add(var)
                    
                    killed.add(var)
        
        # 迭代计算
        reaching = {}  # {(block, idx): vars reaching at this point}
        
        # 初始化
        for block_id, stmts in self.stmts.items():
            for idx in range(len(stmts)):
                reaching[(block_id, idx)] = set()
        
        # 简化的数据流:从入口开始
        changed = True
        while changed:
            changed = False
            
            for block_id, stmts in self.stmts.items():
                # 从前驱继承
                preds = [p for p in self.cfg if block_id in self.cfg.get(p, [])]
                
                reaching_in = set()
                for pred in preds:
                    if self.stmts[pred]:
                        last_idx = len(self.stmts[pred]) - 1
                        reaching_in |= reaching.get((pred, last_idx), set())
                
                for idx, stmt in enumerate(stmts):
                    old = reaching.get((block_id, idx), set())
                    new = reaching_in.copy()
                    
                    # 应用GEN
                    new |= gen.get((block_id, idx), set())
                    
                    # 应用KILL(从之前的)
                    for prev_idx in range(idx):
                        killed_var = kill.get((block_id, prev_idx), set())
                        new -= killed_var
                    
                    if new != old:
                        reaching[(block_id, idx)] = new
                        changed = True
        
        return reaching
    
    def find_dead_assignments(self) -> List[Tuple[int, int]]:
        """
        找出死赋值
        
        Returns:
            [(block_id, stmt_idx), ...] 死赋值列表
        """
        dead_assignments = []
        
        for block_id, stmts in self.stmts.items():
            for idx, stmt in enumerate(stmts):
                if hasattr(stmt, 'lhs'):
                    var = stmt.lhs
                    
                    # 检查是否被使用
                    is_used = False
                    
                    # 检查块内后续语句
                    for later_idx in range(idx + 1, len(stmts)):
                        if hasattr(stmts[later_idx], 'uses'):
                            if var in stmts[later_idx].uses():
                                is_used = True
                                break
                    
                    # 检查后续块
                    if not is_used:
                        for succ in self.cfg.get(block_id, []):
                            # 检查succ块是否使用var
                            if self._block_uses_var(succ, var):
                                is_used = True
                                break
                    
                    # 检查是否是入口块的第一条语句且var可能是输入
                    if not is_used and hasattr(stmt, 'rhs1'):
                        if stmt.rhs1 == 'input':
                            is_used = True
                    
                    if not is_used:
                        dead_assignments.append((block_id, idx))
        
        return dead_assignments
    
    def _block_uses_var(self, block_id: int, var: str) -> bool:
        """检查块是否使用变量"""
        for stmt in self.stmts.get(block_id, []):
            if hasattr(stmt, 'uses') and var in stmt.uses():
                return True
        return False
    
    def eliminate_dead_code(self) -> Dict[int, List]:
        """
        执行死代码消除
        
        Returns:
            优化后的代码
        """
        # 1. 移除不可达块
        unreachable = self.find_unreachable_blocks(0)
        
        # 2. 移除死赋值
        dead_assignments = self.find_dead_assignments()
        
        # 构建优化后的代码
        optimized = {}
        
        for block_id, stmts in self.stmts.items():
            if block_id in unreachable:
                continue
            
            new_stmts = []
            dead_set = set(dead_assignments)
            
            for idx, stmt in enumerate(stmts):
                if (block_id, idx) in dead_set:
                    continue  # 跳过死赋值
                new_stmts.append(stmt)
            
            if new_stmts:
                optimized[block_id] = new_stmts
        
        return optimized


class ControlFlowGraph:
    """控制流图"""
    
    def __init__(self):
        self.blocks = []
        self.edges = defaultdict(list)
    
    def add_block(self, block) -> int:
        block.id = len(self.blocks)
        self.blocks.append(block)
        return block.id
    
    def add_edge(self, from_id: int, to_id: int):
        self.edges[from_id].append(to_id)
    
    def compute_dominators(self, entry: int) -> Dict[int, Set[int]]:
        """计算支配节点"""
        dominators = {i: set(range(len(self.blocks))) for i in range(len(self.blocks))}
        dominators[entry] = {entry}
        
        changed = True
        while changed:
            changed = False
            
            for block in self.blocks:
                new_dom = {block.id}
                
                for pred_id in self.edges:
                    if block.id in self.edges[pred_id]:
                        new_dom &= dominators[pred_id]
                
                new_dom.add(block.id)
                
                if dominators[block.id] != new_dom:
                    dominators[block.id] = new_dom
                    changed = True
        
        return dominators


# 测试代码
if __name__ == "__main__":
    # 测试1: 简单死代码
    print("测试1 - 简单死代码:")
    
    # 模拟简单语句
    class Stmt:
        def __init__(self, lhs, rhs1, rhs2=None, op=None):
            self.lhs = lhs
            self.rhs1 = rhs1
            self.rhs2 = rhs2
            self.op = op
        
        def uses(self):
            result = {self.rhs1}
            if self.rhs2:
                result.add(self.rhs2)
            return result - {self.lhs}
        
        def __repr__(self):
            if self.rhs2:
                return f"{self.lhs} = {self.rhs1} {self.op} {self.rhs2}"
            return f"{self.lhs} = {self.rhs1}"
    
    eliminator = DeadCodeEliminator()
    
    # Block 0: x = 5; y = x + 1; x = 10; z = y
    eliminator.add_block(0, [
        Stmt('x', '5'),
        Stmt('y', 'x', '1', '+'),
        Stmt('x', '10'),  # 死代码? 不,y使用x
        Stmt('z', 'y'),   # y在x被重新赋值后不再使用,所以这个也是死代码
    ])
    
    # 建立CFG
    eliminator.add_edge(0, 1)
    
    # 找出死赋值
    dead = eliminator.find_dead_assignments()
    print(f"  语句: {[str(s) for s in eliminator.stmts[0]]}")
    print(f"  死赋值: {dead}")
    
    # 测试2: 不可达代码
    print("\n测试2 - 不可达代码:")
    
    eliminator2 = DeadCodeEliminator()
    
    # Block 0 -> Block 1
    # Block 0 -> Block 2(死)
    eliminator2.add_block(0, [Stmt('x', '1')])
    eliminator2.add_block(1, [Stmt('y', '2')])
    eliminator2.add_block(2, [Stmt('z', '3')])  # 不可达
    
    eliminator2.add_edge(0, 1)
    eliminator2.add_edge(0, 2)  # 但这使得Block 2可达(假设无条件跳转)
    
    # 如果Block 2真的是不可达的(没有到它的边)
    # 需要重新设置
    eliminator3 = DeadCodeEliminator()
    eliminator3.add_block(0, [Stmt('x', '1')])
    eliminator3.add_block(1, [Stmt('y', '2')])
    eliminator3.add_block(2, [Stmt('z', '3')])
    
    # Block 2没有任何前驱,所以不可达
    eliminator3.add_edge(0, 1)
    
    unreachable = eliminator3.find_unreachable_blocks(0)
    print(f"  不可达块: {unreachable}")
    
    # 测试3: 复杂例子
    print("\n测试3 - 复杂例子:")
    
    eliminator4 = DeadCodeEliminator()
    
    # Block 0: a = input; b = a + 1; c = b + 2
    # Block 1: d = c + 3; e = d + 4
    # Block 2: f = a + b (死代码,因为a和b在后面不再使用)
    
    eliminator4.add_block(0, [
        Stmt('a', 'input'),
        Stmt('b', 'a', '1', '+'),
        Stmt('c', 'b', '2', '+'),
    ])
    
    eliminator4.add_block(1, [
        Stmt('d', 'c', '3', '+'),
        Stmt('e', 'd', '4', '+'),
    ])
    
    eliminator4.add_block(2, [
        Stmt('f', 'a', 'b', '+'),  # 可能不可达或死代码
    ])
    
    eliminator4.add_edge(0, 1)
    eliminator4.add_edge(1, 2)
    
    dead4 = eliminator4.find_dead_assignments()
    print(f"  Block 0死赋值: {[(i, str(eliminator4.stmts[0][i])) for i, _ in dead4 if _ == 0]}")
    print(f"  Block 1死赋值: {[(i, str(eliminator4.stmts[1][i])) for i, _ in dead4 if _ == 1]}")
    print(f"  Block 2死赋值: {[(i, str(eliminator4.stmts[2][i])) for i, _ in dead4 if _ == 2]}")
    
    # 测试4: 验证优化效果
    print("\n测试4 - 优化效果:")
    
    optimized = eliminator4.eliminate_dead_code()
    
    print("  优化前:")
    for bid, stmts in eliminator4.stmts.items():
        print(f"    Block {bid}: {[str(s) for s in stmts]}")
    
    print("  优化后:")
    for bid, stmts in optimized.items():
        print(f"    Block {bid}: {[str(s) for s in stmts]}")
    
    print("\n所有测试完成!")
