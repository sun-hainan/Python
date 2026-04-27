# -*- coding: utf-8 -*-

"""

算法实现：编译器内核 / basic_block



本文件实现 basic_block 相关的算法功能。

"""



from dataclasses import dataclass, field

from typing import List, Dict, Set, Tuple, Optional

from enum import Enum, auto



from intermediate_representation import TACInstruction, OpCode, Address, IRGenerator





@dataclass

class BasicBlock:

    """基本块"""

    block_id: int  # 块ID

    label: str  # 块标签(如果没有则为None)

    instructions: List[TACInstruction] = field(default_factory=list)  # 块内指令

    predecessors: List[int] = field(default_factory=list)  # 前驱块ID列表

    successors: List[int] = field(default_factory=list)  # 后继块ID列表



    def add_instruction(self, instr: TACInstruction):

        """添加指令到块"""

        self.instructions.append(instr)



    def is_empty(self) -> bool:

        """块是否为空"""

        return len(self.instructions) == 0



    def get_last_instruction(self) -> Optional[TACInstruction]:

        """获取最后一条指令"""

        return self.instructions[-1] if self.instructions else None





class BasicBlockBuilder:

    """

    基本块构建器



    算法:

    1. 识别所有基本块的起始位置(leader)

       - 第一条指令是leader

       - 跳转目标指令是leader

       - 跳转后下一条指令是leader

    2. 每个leader到下一个leader(或程序结束)之间的指令构成一个基本块

    """



    def __init__(self):

        self.blocks: List[BasicBlock] = []  # 基本块列表

        self.block_map: Dict[str, int] = {}  # 标签 -> 块ID映射

        self.instructions: List[TACInstruction] = []



    def build(self, instructions: List[TACInstruction]) -> List[BasicBlock]:

        """

        从指令列表构建基本块



        参数:

            instructions: 三地址码指令列表



        返回:

            基本块列表

        """

        self.instructions = instructions

        self.blocks = []

        self.block_map = {}



        if not instructions:

            return []



        # 第一步: 找到所有leader

        leaders = self._find_leaders()



        # 第二步: 根据leader划分基本块

        self._create_blocks(leaders)



        # 第三步: 建立前驱后继关系

        self._build_cfg()



        return self.blocks



    def _find_leaders(self) -> Set[int]:

        """

        找到所有leader的指令索引



        规则:

        1. 第一条指令索引0是leader

        2. 任何跳转指令的目标是leader

        3. 跳转指令的下一条指令是leader

        """

        leaders = {0}  # 起始位置



        for i, instr in enumerate(self.instructions):

            op = instr.op



            # 跳转指令: 目标地址是leader

            if op in [OpCode.JUMP, OpCode.JUMP_IF, OpCode.JUMP_IF_NOT]:

                if instr.result and instr.result.kind == "label":

                    target_label = instr.result.value

                    target_idx = self._find_label_index(target_label)

                    if target_idx is not None:

                        leaders.add(target_idx)



            # 如果是条件跳转,下一条也是leader

            if op in [OpCode.JUMP_IF, OpCode.JUMP_IF_NOT]:

                if i + 1 < len(self.instructions):

                    leaders.add(i + 1)



            # 标签指令后的下一条是leader

            if op == OpCode.LABEL:

                if i + 1 < len(self.instructions):

                    leaders.add(i + 1)



        return leaders



    def _find_label_index(self, label: str) -> Optional[int]:

        """查找标签对应的指令索引"""

        for i, instr in enumerate(self.instructions):

            if instr.op == OpCode.LABEL and instr.result and instr.result.value == label:

                return i

        return None



    def _create_blocks(self, leaders: Set[int]):

        """根据leader创建基本块"""

        sorted_leaders = sorted(leaders)

        sorted_leaders.append(len(self.instructions))  # 添加结束标记



        for i in range(len(sorted_leaders) - 1):

            start_idx = sorted_leaders[i]

            end_idx = sorted_leaders[i + 1]



            block_id = i

            block_label = self._extract_label(start_idx)



            block = BasicBlock(block_id=block_id, label=block_label)



            # 收集块内指令(跳过起始的LABEL指令)

            start_offset = 1 if start_idx > 0 and self.instructions[start_idx].op == OpCode.LABEL else 0

            for j in range(start_idx + start_offset, end_idx):

                block.add_instruction(self.instructions[j])



            self.blocks.append(block)



            # 记录标签到块的映射

            if block_label:

                self.block_map[block_label] = block_id



    def _extract_label(self, index: int) -> Optional[str]:

        """提取指令索引处的标签"""

        if index < len(self.instructions):

            instr = self.instructions[index]

            if instr.op == OpCode.LABEL and instr.result:

                return instr.result.value

        return None



    def _build_cfg(self):

        """构建控制流图(前驱后继关系)"""

        for i, block in enumerate(self.blocks):

            last_instr = block.get_last_instruction()



            if last_instr is None:

                continue



            op = last_instr.op



            # 无条件跳转: 后继是目标块

            if op == OpCode.JUMP:

                if last_instr.result and last_instr.result.kind == "label":

                    target_label = last_instr.result.value

                    if target_label in self.block_map:

                        target_block_id = self.block_map[target_label]

                        block.successors.append(target_block_id)

                        if i not in self.blocks[target_block_id].predecessors:

                            self.blocks[target_block_id].predecessors.append(i)



            # 条件跳转: 后继是目标块和下一块

            elif op in [OpCode.JUMP_IF, OpCode.JUMP_IF_NOT]:

                # 目标块

                if last_instr.result and last_instr.result.kind == "label":

                    target_label = last_instr.result.value

                    if target_label in self.block_map:

                        target_block_id = self.block_map[target_label]

                        block.successors.append(target_block_id)

                        if i not in self.blocks[target_block_id].predecessors:

                            self.blocks[target_block_id].predecessors.append(i)



                # 下一块

                if i + 1 < len(self.blocks):

                    block.successors.append(i + 1)

                    if i + 1 not in self.blocks[i + 1].predecessors:

                        self.blocks[i + 1].predecessors.append(i)



            # 普通指令: 后继是下一块

            elif op not in [OpCode.JUMP, OpCode.JUMP_IF, OpCode.JUMP_IF_NOT,

                           OpCode.RETURN, OpCode.FUNC_END]:

                if i + 1 < len(self.blocks):

                    block.successors.append(i + 1)

                    if i + 1 not in self.blocks[i + 1].predecessors:

                        self.blocks[i + 1].predecessors.append(i)



    def get_block_by_label(self, label: str) -> Optional[BasicBlock]:

        """根据标签获取基本块"""

        if label in self.block_map:

            return self.blocks[self.block_map[label]]

        return None



    def print_blocks(self):

        """打印所有基本块"""

        print("=== 基本块 ===")

        for block in self.blocks:

            print(f"\n--- Block {block.block_id} ---")

            if block.label:

                print(f"  Label: {block.label}")



            print(f"  Predecessors: {block.predecessors}")

            print(f"  Successors: {block.successors}")



            if block.instructions:

                print("  Instructions:")

                for instr in block.instructions:

                    print(f"    {instr}")

            else:

                print("  (empty)")





if __name__ == "__main__":

    # 生成测试IR

    gen = IRGenerator()



    # int max(int a, int b) {

    gen.emit_func_begin("max")

    gen.emit(OpCode.LOAD_PARAM, arg1=Address.temp("a"))

    gen.emit(OpCode.LOAD_PARAM, arg1=Address.temp("b"))



    # if (a > b) goto Ltrue

    gen.emit_binary(OpCode.GT, Address.temp("t1"), Address.temp("a"), Address.temp("b"))

    gen.emit(OpCode.JUMP_IF, result=Address.label("Ltrue"), arg1=Address.temp("t1"))



    # return b;

    gen.emit_return(Address.variable("b"))

    gen.emit_jump("Lend")



    # Ltrue:

    gen.emit_label("Ltrue")

    # return a;

    gen.emit_return(Address.variable("a"))



    # Lend:

    gen.emit_label("Lend")

    gen.emit_func_end("max")



    instructions = gen.generate()



    # 构建基本块

    builder = BasicBlockBuilder()

    blocks = builder.build(instructions)



    # 打印结果

    gen.print_ir()

    print()

    builder.print_blocks()



    # 测试控制流分析

    print("\n=== 控制流分析 ===")

    for block in blocks:

        pred_names = [f"B{p}" for p in block.predecessors]

        succ_names = [f"B{s}" for s in block.successors]

        print(f"B{block.block_id}: preds={pred_names}, succs={succ_names}")

