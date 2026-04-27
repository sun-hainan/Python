# -*- coding: utf-8 -*-
"""
算法实现：编译器优化 / liveness_analysis

本文件实现 liveness_analysis 相关的算法功能。
"""

from typing import List, Set, Dict, Tuple, Optional
from collections import defaultdict


class BasicBlock:
    """基本块"""
    def __init__(self, id: int, statements: List['Statement'] = None):
        self.id = id
        self.statements = statements or []
        self.preds = []  # 前驱块
        self.succs = []  # 后继块
    
    def add_statement(self, stmt: 'Statement'):
        self.statements.append(stmt)
    
    def add_successor(self, block: 'BasicBlock'):
        if block not in self.succs:
            self.succs.append(block)
            block.preds.append(self)
    
    def __repr__(self):
        return f"Block{self.id}"


class Statement:
    """语句基类"""
    pass


class Assign(Statement):
    """赋值语句 x = y 或 x = y op z"""
    def __init__(self, lhs: str, rhs1: str, rhs2: Optional[str] = None, op: Optional[str] = None):
        self.lhs = lhs
        self.rhs1 = rhs1
        self.rhs2 = rhs2  # 如果是二元运算
        self.op = op  # +, -, *, / 等
    
    def uses(self) -> Set[str]:
        """使用的变量"""
        uses = {self.rhs1}
        if self.rhs2:
            uses.add(self.rhs2)
        return uses - {self.lhs}
    
    def defs(self) -> Set[str]:
        """定义的变量"""
        return {self.lhs}
    
    def __repr__(self):
        if self.rhs2:
            return f"{self.lhs} = {self.rhs1} {self.op} {self.rhs2}"
        return f"{self.lhs} = {self.rhs1}"


class ConditionalJump(Statement):
    """条件跳转 if x goto L"""
    def __init__(self, cond: str, target: BasicBlock):
        self.cond = cond
        self.target = target
    
    def uses(self) -> Set[str]:
        return {self.cond}
    
    def defs(self) -> Set[str]:
        return set()
    
    def __repr__(self):
        return f"if {self.cond} goto Block{self.target.id}"


class UnconditionalJump(Statement):
    """无条件跳转 goto L"""
    def __init__(self, target: BasicBlock):
        self.target = target
    
    def uses(self) -> Set[str]:
        return set()
    
    def defs(self) -> Set[str]:
        return set()
    
    def __repr__(self):
        return f"goto Block{self.target.id}"


class Return(Statement):
    """返回语句 return x"""
    def __init__(self, value: Optional[str] = None):
        self.value = value
    
    def uses(self) -> Set[str]:
        return {self.value} if self.value else set()
    
    def defs(self) -> Set[str]:
        return set()
    
    def __repr__(self):
        return f"return {self.value}"


class LivenessAnalyzer:
    """
    活跃变量分析器
    使用数据流方程迭代计算活跃变量
    """
    
    def __init__(self, blocks: List[BasicBlock], variables: Set[str]):
        """
        初始化
        
        Args:
            blocks: 基本块列表
            variables: 所有变量集合
        """
        self.blocks = blocks
        self.variables = variables
        
        # 计算每个块出口处的活跃变量
        self.live_out: Dict[int, Set[str]] = {}
        self.live_in: Dict[int, Set[str]] = {}
    
    def analyze(self, max_iterations: int = 100) -> bool:
        """
        执行活跃变量分析
        
        Args:
            max_iterations: 最大迭代次数
        
        Returns:
            是否收敛
        """
        # 初始化
        for block in self.blocks:
            self.live_out[block.id] = set()
        
        # 迭代直到收敛
        for _ in range(max_iterations):
            changed = False
            
            # 反向遍历块
            for block in reversed(self.blocks):
                # live_out[block] = 合并所有后继块的live_in
                new_live_out = set()
                for succ in block.succs:
                    new_live_out |= self.live_in.get(succ.id, set())
                
                if new_live_out != self.live_out[block.id]:
                    self.live_out[block.id] = new_live_out
                    changed = True
                
                # live_in[block] = uses(block) U (live_out[block] - defs(block))
                uses = set()
                defs = set()
                
                for stmt in block.statements:
                    uses |= stmt.uses()
                    defs |= stmt.defs()
                
                new_live_in = uses | (self.live_out[block.id] - defs)
                
                if new_live_in != self.live_in.get(block.id, set()):
                    self.live_in[block.id] = new_live_in
                    changed = True
            
            if not changed:
                return True
        
        return False
    
    def get_live_vars_before_stmt(self, block: BasicBlock, stmt_idx: int) -> Set[str]:
        """
        获取某语句之前的活跃变量
        
        Args:
            block: 基本块
            stmt_idx: 语句索引
        
        Returns:
            活跃变量集合
        """
        live = self.live_out[block.id].copy()
        
        # 从后向前处理
        for i in range(len(block.statements) - 1, stmt_idx - 1, -1):
            stmt = block.statements[i]
            uses = stmt.uses()
            defs = stmt.defs()
            
            # 如果一个变量被使用且之前不在live中,添加
            live |= uses
            
            # 如果一个变量被定义,从live中移除(除非被后续使用)
            for var in defs:
                if var not in uses:
                    live.discard(var)
        
        return live
    
    def get_live_vars_before(self, block: BasicBlock) -> Set[str]:
        """获取块入口处的活跃变量"""
        return self.live_in.get(block.id, set())
    
    def get_live_vars_after(self, block: BasicBlock) -> Set[str]:
        """获取块出口处的活跃变量"""
        return self.live_out.get(block.id, set())


def build_cfg_from_statements(statements: List[Statement]) -> List[BasicBlock]:
    """
    从语句列表构建控制流图
    
    Args:
        statements: 语句列表
    
    Returns:
        基本块列表
    """
    blocks = []
    current_block = BasicBlock(0)
    blocks.append(current_block)
    
    for stmt in statements:
        current_block.add_statement(stmt)
        
        if isinstance(stmt, (ConditionalJump, UnconditionalJump)):
            # 跳转语句后创建新块
            current_block = BasicBlock(len(blocks))
            blocks.append(current_block)
    
    # 建立前驱后继关系
    for i, block in enumerate(blocks):
        if block.statements:
            last_stmt = block.statements[-1]
            
            if isinstance(last_stmt, ConditionalJump):
                block.add_successor(last_stmt.target)
                if i + 1 < len(blocks):
                    block.add_successor(blocks[i + 1])
            
            elif isinstance(last_stmt, UnconditionalJump):
                block.add_successor(last_stmt.target)
    
    return blocks


# 测试代码
if __name__ == "__main__":
    # 测试1: 简单程序
    print("测试1 - 简单程序:")
    
    # 程序:
    # 1: a = 0
    # 2: b = a + 1
    # 3: c = c + b
    # 4: if c < 100 goto 2
    
    blocks = [
        BasicBlock(0, [
            Assign('a', '0'),
            Assign('b', 'a', '1', '+'),
            Assign('c', 'c', 'b', '+'),
            ConditionalJump('c', None),  # 临时,稍后设置目标
        ])
    ]
    
    # 设置跳转目标
    blocks[0].statements[-1].target = blocks[0]
    
    # 添加后继
    blocks[0].add_successor(blocks[0])
    
    variables = {'a', 'b', 'c'}
    
    analyzer = LivenessAnalyzer(blocks, variables)
    analyzer.analyze()
    
    print(f"  块0出口活跃: {analyzer.get_live_vars_after(blocks[0])}")
    
    # 测试2: 复杂程序
    print("\n测试2 - 复杂程序:")
    
    # 程序:
    # Block0: x = input
    # Block1: if x > 0 goto Block2 else Block3
    # Block2: y = x * 2
    # Block3: y = x + 1
    # Block4: z = y + 1
    # Block5: output z
    
    b0 = BasicBlock(0, [Assign('x', 'input')])
    b1 = BasicBlock(1, [ConditionalJump('x', None)])  # target稍后设置
    b2 = BasicBlock(2, [Assign('y', 'x', '2', '*')])
    b3 = BasicBlock(3, [Assign('y', 'x', '1', '+')])
    b4 = BasicBlock(4, [Assign('z', 'y', '1', '+')])
    b5 = BasicBlock(5, [Return('z')])
    
    # 建立CFG
    b0.add_successor(b1)
    b1.target = b2  # 条件为真时跳转到b2
    b1.add_successor(b2)
    b1.add_successor(b3)
    b2.add_successor(b4)
    b3.add_successor(b4)
    b4.add_successor(b5)
    
    blocks2 = [b0, b1, b2, b3, b4, b5]
    variables2 = {'x', 'y', 'z', 'input', 'output'}
    
    analyzer2 = LivenessAnalyzer(blocks2, variables2)
    analyzer2.analyze()
    
    print("  活跃变量分析结果:")
    for block in blocks2:
        print(f"    Block{block.id}: in={analyzer2.get_live_vars_before(block)}, out={analyzer2.get_live_vars_after(block)}")
    
    # 测试3: 使用活跃变量进行寄存器分配决策
    print("\n测试3 - 寄存器压力分析:")
    
    # 找出每个点需要同时活跃的变量数
    max_live = 0
    for block in blocks2:
        live_at_exit = analyzer2.get_live_vars_after(block)
        live_vars = live_at_exit & variables2 - {'input', 'output'}
        max_live = max(max_live, len(live_vars))
    
    print(f"  最大同时活跃变量数: {max_live}")
    print(f"  建议寄存器数: {max_live + 2}")  # +2是安全余量
    
    # 测试4: 验证活跃变量分析
    print("\n测试4 - 验证:")
    for block in blocks2:
        live_in = analyzer2.get_live_vars_before(block)
        live_out = analyzer2.get_live_vars_after(block)
        
        # 计算块内def和use
        defs = set()
        uses = set()
        for stmt in block.statements:
            uses |= stmt.uses()
            defs |= stmt.defs()
        
        # 验证数据流方程
        expected_live_in = uses | (live_out - defs)
        print(f"  Block{block.id}: live_in={live_in}, expected={expected_live_in}, match={live_in == expected_live_in}")
    
    print("\n所有测试完成!")
