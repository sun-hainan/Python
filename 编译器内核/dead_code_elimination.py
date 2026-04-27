# -*- coding: utf-8 -*-
"""
算法实现：编译器内核 / dead_code_elimination

本文件实现 dead_code_elimination 相关的算法功能。
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field

# ========== 指令和基本块 ==========

@dataclass
class Instruction:
    """指令"""
    opcode: str
    result: Optional[str] = None
    arg1: Optional[str] = None
    arg2: Optional[str] = None
    label: Optional[str] = None
    is_critical: bool = False  # 是否是关键指令（如store、return）
    
    def __repr__(self):
        parts = []
        if self.result:
            parts.append(f"{self.result} = ")
        if self.arg1 and self.arg2:
            parts.append(f"{self.arg1} {self.opcode} {self.arg2}")
        elif self.arg1:
            parts.append(f"{self.opcode} {self.arg1}")
        else:
            parts.append(self.opcode)
        return "".join(parts)


@dataclass
class BasicBlock:
    """基本块"""
    label: str
    instructions: List[Instruction] = field(default_factory=list)
    predecessors: List['BasicBlock'] = field(default_factory=list)
    successors: List['BasicBlock'] = field(default_factory=list)


# ========== 活跃性分析 ==========

class LivenessAnalyzer:
    """
    活跃性分析器
    确定每个变量的活跃范围
    """
    
    def __init__(self, cfg):
        self.cfg = cfg
        self.live_in: Dict[str, Set[str]] = {}   # block -> live variables
        self.live_out: Dict[str, Set[str]] = {}  # block -> live variables
    
    def analyze(self) -> Dict[str, Set[str]]:
        """
        执行活跃性分析
        返回: 每个块的IN集合
        """
        # 初始化
        for block in self.cfg.blocks:
            self.live_in[block.label] = set()
            self.live_out[block.label] = set()
        
        # 迭代直到收敛
        changed = True
        iterations = 0
        
        while changed and iterations < 100:
            changed = False
            iterations += 1
            
            for block in reversed(self.cfg.blocks):
                old_in = self.live_in[block.label].copy()
                
                # 计算OUT
                new_out = set()
                for succ in block.successors:
                    new_out |= self.live_in.get(succ.label, set())
                self.live_out[block.label] = new_out
                
                # 计算IN
                new_in = self._compute_in(block)
                
                if new_in != old_in:
                    self.live_in[block.label] = new_in
                    changed = True
        
        return self.live_in
    
    def _compute_in(self, block: BasicBlock) -> Set[str]:
        """计算块的IN集合"""
        live = self.live_out[block.label].copy()
        
        # 反向扫描指令
        for instr in reversed(block.instructions):
            if instr.result:
                # 结果变为不活跃
                live.discard(instr.result)
            
            # 操作数变为活跃
            if instr.arg1:
                live.add(instr.arg1)
            if instr.arg2:
                live.add(instr.arg2)
        
        return live


# ========== 死代码消除 ==========

class DeadCodeEliminator:
    """
    死代码消除器（DCE）
    移除不会被使用的计算
    """
    
    def __init__(self, cfg):
        self.cfg = cfg
        self.liveness_analyzer = LivenessAnalyzer(cfg)
        self.dead_instructions: List[Instruction] = []
        self.stats = {"removed": 0, "kept": 0}
    
    def eliminate(self) -> List[BasicBlock]:
        """
        执行死代码消除
        返回: 优化后的基本块列表
        """
        # 1. 分析活跃性
        live_in = self.liveness_analyzer.analyze()
        
        # 2. 标记和移除死代码
        for block in self.cfg.blocks:
            self._process_block(block, live_in)
        
        return self.cfg.blocks
    
    def _process_block(self, block: BasicBlock, live_in: Dict[str, Set[str]]):
        """处理基本块"""
        i = 0
        while i < len(block.instructions):
            instr = block.instructions[i]
            
            # 检查是否是死代码
            if self._is_dead(instr, block, live_in):
                self.dead_instructions.append(instr)
                block.instructions.pop(i)
                self.stats["removed"] += 1
            else:
                self.stats["kept"] += 1
                i += 1
    
    def _is_dead(self, instr: Instruction, block: BasicBlock, 
                 live_in: Dict[str, Set[str]]) -> bool:
        """检查指令是否死代码"""
        # 关键指令不能删除
        if instr.is_critical:
            return False
        
        # 没有结果的指令（如跳转、store）
        if not instr.result:
            return False
        
        # 检查结果是否在后续活跃
        live_vars = live_in.get(block.label, set())
        
        # 需要考虑指令本身的副作用
        if instr.opcode == "call":
            return False  # 函数调用可能有副作用
        
        return instr.result not in live_vars


class AggressiveDCE:
    """
    激进死代码消除
    处理更多边缘情况
    """
    
    def __init__(self, cfg):
        self.cfg = cfg
        self.removed_count = 0
    
    def run(self) -> List[BasicBlock]:
        """运行激进DCE"""
        changed = True
        
        while changed:
            changed = False
            
            # 重新计算活跃性
            analyzer = LivenessAnalyzer(self.cfg)
            live_in = analyzer.analyze()
            
            # 移除死代码
            for block in self.cfg.blocks:
                i = 0
                while i < len(block.instructions):
                    instr = block.instructions[i]
                    
                    if self._is_dead(instr, block, live_in):
                        block.instructions.pop(i)
                        self.removed_count += 1
                        changed = True
                    else:
                        i += 1
            
            # 重新分析（活跃性会改变）
            if changed:
                analyzer = LivenessAnalyzer(self.cfg)
                live_in = analyzer.analyze()
        
        return self.cfg.blocks
    
    def _is_dead(self, instr: Instruction, block: BasicBlock,
                 live_in: Dict[str, Set[str]]) -> bool:
        """检查是否死代码"""
        if instr.is_critical or not instr.result:
            return False
        
        # 检查结果是否在出口活跃
        if instr.result not in live_in.get(block.label, set()):
            # 检查是否有副作用
            if self._has_side_effects(instr):
                return False
            return True
        
        return False
    
    def _has_side_effects(self, instr: Instruction) -> bool:
        """检查是否有副作用"""
        side_effect_ops = {"store", "call", "throw", "invoke"}
        
        if instr.opcode in side_effect_ops:
            return True
        
        # 某些操作有隐式副作用
        if instr.opcode == "div" and instr.arg2 == "0":
            return True
        
        return False


# ========== 活跃性驱动的DCE ==========

class LivenessDrivenDCE:
    """
    活跃性驱动的死代码消除
    结合活跃性分析和控制流分析
    """
    
    def __init__(self, cfg):
        self.cfg = cfg
        self.live_vars: Set[str] = set()
        self.cfg_changed: bool = True  # 控制流是否改变
    
    def run(self) -> 'LivenessDrivenDCE':
        """运行DCE"""
        while self.cfg_changed:
            self.cfg_changed = False
            
            # 步骤1：计算活跃性
            self._compute_liveness()
            
            # 步骤2：消除基本块内的死代码
            self._remove_dead_assignments()
            
            # 步骤3：消除不可达基本块
            self._remove_unreachable_blocks()
        
        return self
    
    def _compute_liveness(self):
        """计算活跃性"""
        analyzer = LivenessAnalyzer(self.cfg)
        live_in = analyzer.analyze()
        
        # 合并所有块的活跃变量
        all_live = set()
        for live_set in live_in.values():
            all_live |= live_set
        
        self.live_vars = all_live
    
    def _remove_dead_assignments(self):
        """移除死赋值"""
        for block in self.cfg.blocks:
            i = 0
            while i < len(block.instructions):
                instr = block.instructions[i]
                
                if (instr.result and 
                    instr.opcode not in ("store", "call", "invoke") and
                    instr.result not in self.live_vars):
                    
                    block.instructions.pop(i)
                    self.cfg_changed = True
                else:
                    i += 1
    
    def _remove_unreachable_blocks(self):
        """移除不可达块"""
        reachable = self._find_reachable_blocks()
        
        new_blocks = []
        for block in self.cfg.blocks:
            if block.label in reachable:
                new_blocks.append(block)
        
        if len(new_blocks) != len(self.cfg.blocks):
            self.cfg.blocks = new_blocks
            self.cfg_changed = True


# ========== 条件死代码消除 ==========

class ConditionalDCE:
    """
    条件死代码消除
    处理条件分支的死代码
    """
    
    def __init__(self, cfg):
        self.cfg = cfg
    
    def optimize(self) -> 'ConditionalDCE':
        """优化条件分支"""
        for block in self.cfg.blocks:
            self._optimize_block(block)
        
        return self
    
    def _optimize_block(self, block: BasicBlock):
        """优化基本块"""
        # 查找条件分支
        for i, instr in enumerate(block.instructions):
            if instr.opcode.startswith("j") and instr.label:
                # 条件跳转
                self._handle_conditional_jump(block, instr)
    
    def _handle_conditional_jump(self, block: BasicBlock, instr: Instruction):
        """处理条件跳转"""
        # 简化：检查是否能简化条件
        pass


if __name__ == "__main__":
    print("=" * 60)
    print("死代码消除（DCE）演示")
    print("=" * 60)
    
    # 创建测试代码
    print("\n原代码:")
    code = [
        Instruction("add", "t0", "a", "b"),     # t0 = a + b
        Instruction("mul", "t1", "t0", "c"),    # t1 = t0 * c
        Instruction("add", "t2", "t0", "d"),    # t2 = t0 + d  <- t2之后不再使用
        Instruction("sub", "t3", "t1", "t2"),   # t3 = t1 - t2  <- t2已被使用
        Instruction("store", result=None, arg1="[x]", arg2="t3"),  # store [x] = t3
        Instruction("ret", arg1="t3"),          # return t3
    ]
    
    for instr in code:
        print(f"  {instr}")
    
    # 创建CFG（简化）
    block = BasicBlock(
        label="entry",
        instructions=code
    )
    
    print("\n--- 活跃性分析 ---")
    analyzer = LivenessAnalyzer(type('CFG', (), {'blocks': [block]})())
    live_in = analyzer.analyze()
    
    print(f"入口块活跃变量: {live_in.get('entry', set())}")
    
    print("\n--- 死代码消除 ---")
    dce = DeadCodeEliminator(type('CFG', (), {'blocks': [block]})())
    dce.eliminate()
    
    print("消除后代码:")
    for instr in block.instructions:
        print(f"  {instr}")
    
    print(f"\n统计: 移除={dce.stats['removed']}, 保留={dce.stats['kept']}")
    
    # 活跃性驱动的DCE示例
    print("\n--- 活跃性驱动的DCE ---")
    
    print("示例场景:")
    print("  原: t0 = a + b; t1 = t0 * 2; t2 = t1 + 3; x = t2")
    print("  活跃变量: {a, b, x}")
    print("  优化后: 直接 x = (a + b) * 2 + 3  # t0, t1, t2被消除")
    
    print("\nDCE策略:")
    print("  1. 活跃性分析：从出口回溯，确定每个变量的活跃范围")
    print("  2. 死赋值消除：移除结果不活跃且无副作用的赋值")
    print("  3. 不可达块消除：移除从入口无法到达的块")
    print("  4. 循环：直到不再变化")
    
    print("\nDCE注意事项:")
    print("  - 必须保留有副作用的指令（store, call）")
    print("  - 必须保留控制流指令（branch, ret）")
    print("  - 活跃性分析需要迭代直到收敛")
