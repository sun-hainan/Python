# -*- coding: utf-8 -*-

"""

算法实现：编译器内核 / loop_optimization



本文件实现 loop_optimization 相关的算法功能。

"""



from typing import List, Dict, Set, Tuple, Optional

from dataclasses import dataclass, field



# ========== 循环结构定义 ==========



@dataclass

class Loop:

    """循环结构"""

    header_block: str           # 循环头块

    latch_block: str           # 循环Latch块（回到头部的块）

    body_blocks: List[str]      # 循环体块

    exit_blocks: List[str]     # 出口块

    preheader_block: Optional[str] = None  # 前置块

    induction_vars: List[str] = field(default_factory=list)  # 归纳变量

    

    def __repr__(self):

        return f"Loop(header={self.header_block}, body={len(self.body_blocks)} blocks)"





@dataclass

class Instruction:

    """指令"""

    opcode: str

    result: Optional[str] = None

    arg1: Optional[str] = None

    arg2: Optional[str] = None

    label: Optional[str] = None





# ========== 循环不变代码外提 (Loop-Invariant Code Motion) ==========



class LoopInvariantCodeMotion:

    """

    循环不变代码外提

    将不变计算从循环内移到循环外

    """

    

    def __init__(self, cfg):

        self.cfg = cfg

        self.loop_analyzer = LoopAnalyzer(cfg)

        self.moved_instructions: List[Tuple[str, Instruction]] = []  # (target_block, instr)

    

    def optimize(self) -> 'LoopInvariantCodeMotion':

        """执行LICM"""

        # 找出所有循环

        loops = self.loop_analyzer.find_loops()

        

        for loop in loops:

            self._process_loop(loop)

        

        return self

    

    def _process_loop(self, loop: Loop):

        """处理单个循环"""

        # 找出循环不变指令

        invariant_instrs = self._find_invariant_instructions(loop)

        

        if not invariant_instrs:

            return

        

        # 移到前置块

        if loop.preheader_block:

            self._move_to_preheader(loop, invariant_instrs)

    

    def _find_invariant_instructions(self, loop: Loop) -> List[Instruction]:

        """找出循环不变指令"""

        invariant = []

        loop_vars = set(loop.induction_vars)

        

        for block_label in loop.body_blocks:

            block = self.cfg.get_block_by_label(block_label)

            if not block:

                continue

            

            for instr in block.instructions:

                if self._is_invariant(instr, loop_vars):

                    invariant.append((block_label, instr))

                    # 更新循环变量集合

                    if instr.result:

                        loop_vars.add(instr.result)

        

        return invariant

    

    def _is_invariant(self, instr: Instruction, loop_vars: Set[str]) -> bool:

        """检查指令是否循环不变"""

        # 计算指令的依赖

        dependencies = set()

        if instr.arg1:

            dependencies.add(instr.arg1)

        if instr.arg2:

            dependencies.add(instr.arg2)

        

        # 如果所有依赖都不在循环变量中，则是循环不变的

        for dep in dependencies:

            if dep in loop_vars:

                return False

        

        # 检查是否是内存相关指令

        if instr.opcode in ("load", "store"):

            return False

        

        return True

    

    def _move_to_preheader(self, loop: Loop, instructions: List[Tuple[str, Instruction]]):

        """将指令移到前置块"""

        for block_label, instr in instructions:

            self.moved_instructions.append((loop.preheader_block or "preheader", instr))





# ========== 循环展开 (Loop Unrolling) ==========



class LoopUnroller:

    """

    循环展开

    减少循环控制开销，增加指令级并行

    """

    

    def __init__(self, cfg):

        self.cfg = cfg

        self.unroll_factor = 2  # 默认展开因子

    

    def unroll(self, loop: Loop, factor: int = 2) -> List[Instruction]:

        """

        展开循环

        返回: 新的指令序列

        """

        body_instrs = self._get_loop_body(loop)

        trip_count = self._estimate_trip_count(loop)

        

        if trip_count and trip_count < factor:

            # 循环次数太小，不展开

            return self._get_loop_instructions(loop)

        

        result = []

        

        # 复制循环体factor次

        for i in range(factor):

            for instr in body_instrs:

                # 重命名指令结果（避免冲突）

                new_instr = self._clone_instr(instr, suffix=f"_u{i}")

                result.append(new_instr)

        

        # 如果是固定次数循环，移除循环分支

        # 否则保留原循环

        return result

    

    def _get_loop_body(self, loop: Loop) -> List[Instruction]:

        """获取循环体指令"""

        body_instrs = []

        

        for block_label in loop.body_blocks:

            block = self.cfg.get_block_by_label(block_label)

            if block:

                body_instrs.extend(block.instructions)

        

        return body_instrs

    

    def _estimate_trip_count(self, loop: Loop) -> Optional[int]:

        """估算循环次数（如果可确定）"""

        # 简化：返回None表示未知

        return None

    

    def _clone_instr(self, instr: Instruction, suffix: str = "") -> Instruction:

        """克隆指令（可能需要重命名）"""

        result = instr.result + suffix if instr.result else None

        return Instruction(

            opcode=instr.opcode,

            result=result,

            arg1=instr.arg1,

            arg2=instr.arg2,

            label=instr.label

        )

    

    def _get_loop_instructions(self, loop: Loop) -> List[Instruction]:

        """获取循环的所有指令"""

        return self._get_loop_body(loop)





# ========== 循环交换 (Loop Interchange) ==========



class LoopInterchanger:

    """

    循环交换

    交换嵌套循环的顺序以改善缓存局部性

    """

    

    def __init__(self, cfg):

        self.cfg = cfg

    

    def can_interchange(self, outer_loop: Loop, inner_loop: Loop) -> bool:

        """

        检查是否可以交换

        依赖：内层循环的迭代不依赖于外层循环的迭代变量

        """

        # 检查内层循环的归纳变量是否依赖外层循环

        for inner_var in inner_loop.induction_vars:

            for outer_var in outer_loop.induction_vars:

                if self._depends(inner_var, outer_var):

                    return False

        

        return True

    

    def _depends(self, var1: str, var2: str) -> bool:

        """检查变量依赖"""

        # 简化实现

        return var1 == var2

    

    def interchange(self, nested_loop: Tuple[Loop, Loop]) -> Tuple[Loop, Loop]:

        """交换内外层循环"""

        outer_loop, inner_loop = nested_loop

        

        # 交换角色

        new_outer = Loop(

            header_block=inner_loop.header_block,

            latch_block=inner_loop.latch_block,

            body_blocks=inner_loop.body_blocks,

            exit_blocks=inner_loop.exit_blocks,

            preheader_block=inner_loop.preheader_block,

            induction_vars=inner_loop.induction_vars

        )

        

        new_inner = Loop(

            header_block=outer_loop.header_block,

            latch_block=outer_loop.latch_block,

            body_blocks=outer_loop.body_blocks,

            exit_blocks=outer_loop.exit_blocks,

            preheader_block=outer_loop.preheader_block,

            induction_vars=outer_loop.induction_vars

        )

        

        return new_outer, new_inner





# ========== 循环合并 (Loop Fusion) ==========



class LoopFusor:

    """

    循环合并

    将两个相邻的同方向循环合并为一个

    """

    

    def __init__(self, cfg):

        self.cfg = cfg

        self.loop_analyzer = LoopAnalyzer(cfg)

    

    def can_fuse(self, loop1: Loop, loop2: Loop) -> bool:

        """

        检查是否可以合并

        条件：

        1. 循环必须相邻

        2. 循环必须同方向（都是计数循环或都是while循环）

        3. 循环之间没有数据依赖

        """

        # 检查是否相邻

        if not self._are_adjacent(loop1, loop2):

            return False

        

        # 检查数据依赖

        if self._has_dependence(loop1, loop2):

            return False

        

        # 检查循环结构兼容

        if loop1.induction_vars != loop2.induction_vars:

            return False

        

        return True

    

    def _are_adjacent(self, loop1: Loop, loop2: Loop) -> bool:

        """检查两个循环是否相邻"""

        # loop1的出口后直接是loop2的入口

        for exit_block in loop1.exit_blocks:

            exit = self.cfg.get_block_by_label(exit_block)

            if exit and loop2.header_block in [s.label for s in exit.successors]:

                return True

        return False

    

    def _has_dependence(self, loop1: Loop, loop2: Loop) -> bool:

        """检查循环间是否有数据依赖"""

        # 简化：假设没有依赖

        return False

    

    def fuse(self, loop1: Loop, loop2: Loop) -> Loop:

        """合并两个循环"""

        fused = Loop(

            header_block=loop1.header_block,

            latch_block=loop2.latch_block,

            body_blocks=loop1.body_blocks + loop2.body_blocks,

            exit_blocks=loop2.exit_blocks,

            preheader_block=loop1.preheader_block,

            induction_vars=loop1.induction_vars

        )

        

        return fused





# ========== 循环分析器 ==========



class LoopAnalyzer:

    """

    循环分析器

    识别CFG中的循环结构

    """

    

    def __init__(self, cfg):

        self.cfg = cfg

        self.loops: List[Loop] = []

    

    def find_loops(self) -> List[Loop]:

        """找出所有循环"""

        self.loops = []

        

        # 简化：基于回边检测

        back_edges = self._find_back_edges()

        

        for header, latch in back_edges:

            loop = self._construct_loop(header, latch)

            if loop:

                self.loops.append(loop)

        

        return self.loops

    

    def _find_back_edges(self) -> List[Tuple[str, str]]:

        """找出所有回边（Back Edges）"""

        back_edges = []

        

        for block in self.cfg.blocks:

            for succ in block.successors:

                if self._dominates(succ, block):

                    # succ支配block，所以这是一个回边

                    back_edges.append((succ.label, block.label))

        

        return back_edges

    

    def _dominates(self, dominator: 'Block', node: 'Block') -> bool:

        """检查是否支配"""

        # 简化：假设支配关系已知

        return False

    

    def _construct_loop(self, header_label: str, latch_label: str) -> Optional[Loop]:

        """构建循环结构"""

        # 找出循环体

        body_blocks = self._find_loop_blocks(header_label, latch_label)

        

        if not body_blocks:

            return None

        

        # 找出出口块

        exit_blocks = self._find_exit_blocks(header_label, body_blocks)

        

        return Loop(

            header_block=header_label,

            latch_block=latch_label,

            body_blocks=body_blocks,

            exit_blocks=exit_blocks,

            preheader_block=None

        )

    

    def _find_loop_blocks(self, header: str, latch: str) -> List[str]:

        """找出循环内的所有块"""

        body = [header]

        

        # 使用DFS找出所有能到达header且不离开循环的块

        visited = set()

        stack = [latch]

        

        while stack:

            block_label = stack.pop()

            if block_label in visited:

                continue

            visited.add(block_label)

            

            if block_label == header:

                continue

            

            body.append(block_label)

            

            block = self.cfg.get_block_by_label(block_label)

            if block:

                for succ in block.successors:

                    if succ.label != header and succ.label not in visited:

                        stack.append(succ.label)

        

        return list(visited)

    

    def _find_exit_blocks(self, header: str, body_blocks: List[str]) -> List[str]:

        """找出循环出口块"""

        exits = []

        

        for block_label in body_blocks:

            block = self.cfg.get_block_by_label(block_label)

            if block:

                for succ in block.successors:

                    if succ.label not in body_blocks:

                        exits.append(block_label)

                        break

        

        return exits





# ========== 主循环优化器 ==========



class LoopOptimizer:

    """

    主循环优化器

    协调多种循环优化

    """

    

    def __init__(self, cfg):

        self.cfg = cfg

        self.licm = LoopInvariantCodeMotion(cfg)

        self.unroller = LoopUnroller(cfg)

        self.interchanger = LoopInterchanger(cfg)

        self.fusor = LoopFusor(cfg)

    

    def optimize(self) -> 'LoopOptimizer':

        """执行所有循环优化"""

        # 1. 循环不变代码外提

        self.licm.optimize()

        

        # 2. 循环展开

        analyzer = LoopAnalyzer(self.cfg)

        loops = analyzer.find_loops()

        

        for loop in loops:

            # 可以选择性地展开

            pass

        

        return self

    

    def get_optimizations(self) -> Dict[str, List]:

        """获取已执行的优化"""

        return {

            "licm": self.licm.moved_instructions,

            "unrolls": [],

            "interchanges": [],

            "fusions": []

        }





if __name__ == "__main__":

    print("=" * 60)

    print("循环优化演示")

    print("=" * 60)

    

    print("\n循环优化类型:")

    

    print("\n1. 循环不变代码外提 (LICM):")

    print("   原:")

    print("     for i in range(n):")

    print("         x = a[i]")

    print("         y = z + 10  # z不依赖循环")

    print("         b[i] = x + y")

    print("   优化后:")

    print("     y = z + 10  # 外提")

    print("     for i in range(n):")

    print("         x = a[i]")

    print("         b[i] = x + y")

    

    print("\n2. 循环展开:")

    print("   原:")

    print("     for i in range(4):")

    print("         a[i] = b[i] * 2")

    print("   优化后:")

    print("     a[0] = b[0] * 2")

    print("     a[1] = b[1] * 2")

    print("     a[2] = b[2] * 2")

    print("     a[3] = b[3] * 2")

    

    print("\n3. 循环交换:")

    print("   改善缓存局部性")

    print("   A[i][j] -> A[j][i] 访问模式改变")

    

    print("\n4. 循环合并:")

    print("   原:")

    print("     for i in range(n):")

    print("         a[i] = b[i] + 1")

    print("     for i in range(n):")

    print("         c[i] = a[i] * 2")

    print("   优化后:")

    print("     for i in range(n):")

    print("         a[i] = b[i] + 1")

    print("         c[i] = a[i] * 2")

    

    print("\n5. 归纳变量优化:")

    print("   识别并优化循环计数变量")

    

    print("\n循环优化重要性:")

    print("  - 减少循环开销（分支预测失败、迭代计数）")

    print("  - 改善数据局部性（缓存友好）")

    print("  - 增加指令级并行（ILP）")

    print("  - 暴露更多优化机会")

