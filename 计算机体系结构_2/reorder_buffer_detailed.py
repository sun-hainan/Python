# -*- coding: utf-8 -*-

"""

算法实现：计算机体系结构_2 / reorder_buffer_detailed



本文件实现 reorder_buffer_detailed 相关的算法功能。

"""



import random

from typing import List, Optional, Dict, Set, Tuple

from dataclasses import dataclass, field

from enum import Enum, auto





class ROB_Entry_State(Enum):

    """ROB条目状态"""

    PENDING = auto()       # 等待执行

    EXECUTING = auto()     # 正在执行

    COMPLETED = auto()     # 执行完成

    SQUASHED = auto()      # 被取消

    COMMITTED = auto()     # 已提交





class Instruction_Type(Enum):

    """指令类型"""

    ALU = auto()

    LOAD = auto()

    STORE = auto()

    BRANCH = auto()

    CALL = auto()

    RET = auto()





@dataclass

class ROB_Entry:

    """ROB条目"""

    id: int = 0                       # 条目ID

    instruction_pc: int = 0           # 指令PC

    instr_type: Instruction_Type = Instruction_Type.ALU

    dest_phys_reg: Optional[int] = None  # 目的物理寄存器

    dest_logical_reg: Optional[int] = None  # 目的逻辑寄存器

    result_value: Optional[int] = None # 执行结果

    exception: bool = False            # 是否发生异常

    mispredicted: bool = False        # 分支是否预测错误

    target_pc: int = 0                # 分支目标PC

    state: ROB_Entry_State = ROB_Entry_State.PENDING

    age: int = 0                      # 条目年龄（程序顺序）





class Rename_Map_Table:

    """寄存器重命名映射表"""

    def __init__(self, num_logical: int = 16):

        self.num_logical = num_logical

        self.map_table: Dict[int, int] = {i: i for i in range(num_logical)}  # 逻辑->物理

        self.pending_free: List[int] = []  # 待释放的物理寄存器





    def get_phys(self, logical: int) -> int:

        """查询逻辑寄存器对应的物理寄存器"""

        return self.map_table.get(logical, logical)





    def rename(self, logical: int, new_phys: int, old_phys: int):

        """更新映射"""

        self.map_table[logical] = new_phys

        if old_phys is not None and old_phys >= self.num_logical:

            self.pending_free.append(old_phys)





    def restore(self, logical: int, old_phys: int):

        """恢复旧映射"""

        if old_phys is not None:

            self.map_table[logical] = old_phys





class Reorder_Buffer:

    """重排序缓冲"""

    def __init__(self, size: int = 32):

        self.size = size

        self.buffer: List[Optional[ROB_Entry]] = [None] * size

        self.head: int = 0          # 最老条目（提交位置）

        self.tail: int = 0          # 最新条目

        self.count: int = 0

        self.next_id: int = 0

        # 重命名映射表

        self.rename_map = Rename_Map_Table(num_logical=16)

        # 物理寄存器文件

        self.phys_reg_file: List[Optional[int]] = [None] * 64

        self.phys_reg_valid: List[bool] = [False] * 64

        # 统计

        self.committed_count: int = 0

        self.squashed_count: int = 0





    def is_full(self) -> bool:

        """ROB是否已满"""

        return self.count >= self.size





    def is_empty(self) -> bool:

        """ROB是否为空"""

        return self.count == 0





    def _advance(self, idx: int) -> int:

        """环形索引前进"""

        return (idx + 1) % self.size





    def allocate(self) -> Optional[int]:

        """分配一个新的ROB条目"""

        if self.is_full():

            return None

        entry_id = self.next_id

        self.next_id += 1

        entry = ROB_Entry(id=entry_id, age=self.count)

        self.buffer[self.tail] = entry

        self.tail = self._advance(self.tail)

        self.count += 1

        return entry_id





    def get_entry(self, entry_id: int) -> Optional[ROB_Entry]:

        """根据ID获取ROB条目"""

        for entry in self.buffer:

            if entry is not None and entry.id == entry_id:

                return entry

        return None





    def write_result(self, entry_id: int, value: int):

        """写入执行结果"""

        entry = self.get_entry(entry_id)

        if entry is not None:

            entry.result_value = value

            entry.state = ROB_Entry_State.COMPLETED

            # 如果有目的寄存器，写入物理寄存器文件

            if entry.dest_phys_reg is not None:

                self.phys_reg_file[entry.dest_phys_reg] = value

                self.phys_reg_valid[entry.dest_phys_reg] = True





    def commit_ready(self) -> bool:

        """检查头部是否准备好提交"""

        if self.is_empty():

            return False

        entry = self.buffer[self.head]

        return entry is not None and entry.state == ROB_Entry_State.COMPLETED





    def commit(self) -> Optional[ROB_Entry]:

        """提交一条指令"""

        if not self.commit_ready():

            return None

        entry = self.buffer[self.head]

        self.buffer[self.head] = None

        self.head = self._advance(self.head)

        self.count -= 1

        entry.state = ROB_Entry_State.COMMITTED

        self.committed_count += 1

        # 释放旧的物理寄存器（如果需要）

        # 这里简化处理：对于ALU/LOAD指令，提交时不需要特殊处理

        return entry





    def squash_from(self, entry_id: int):

        """Squash从某个条目开始的所有指令"""

        idx = self.head

        squashed = 0

        while idx != self.tail:

            entry = self.buffer[idx]

            if entry is not None:

                if entry.id >= entry_id:

                    # 恢复寄存器映射

                    if entry.dest_logical_reg is not None and entry.dest_phys_reg is not None:

                        # 简化：假设我们保存了旧映射

                        pass

                    entry.state = ROB_Entry_State.SQUASHED

                    squashed += 1

            idx = self._advance(idx)

        self.squashed_count += squashed





    def squash_branch(self, entry_id: int, correct_pc: int):

        """分支预测失败时的squash"""

        # 先squash该分支及其后续指令

        self.squash_from(entry_id)

        # 返回正确PC（交给前端重置）





class ROB_Processor:

    """使用ROB的简化处理器模型"""

    def __init__(self, rob_size: int = 16):

        self.rob = Reorder_Buffer(size=rob_size)

        self.pc: int = 0x1000

        self.cycles: int = 0

        self.total_instructions: int = 0





    def issue_instruction(self, instr_type: Instruction_Type, dest_logical: Optional[int] = None) -> Optional[int]:

        """发射一条指令到ROB"""

        entry_id = self.rob.allocate()

        if entry_id is None:

            return None

        entry = self.rob.get_entry(entry_id)

        entry.instr_type = instr_type

        entry.instruction_pc = self.pc

        entry.dest_logical_reg = dest_logical

        # 寄存器重命名

        if dest_logical is not None:

            # 分配新物理寄存器

            old_phys = None

            for i in range(16, 64):

                if not self.rob.phys_reg_valid[i]:

                    old_phys = self.rob.rename_map.get_phys(dest_logical)

                    self.rob.rename_map.rename(dest_logical, i, old_phys)

                    entry.dest_phys_reg = i

                    break

        self.pc += 4

        self.total_instructions += 1

        return entry_id





    def execute_instruction(self, entry_id: int, result: int):

        """执行指令并写入结果"""

        self.rob.write_result(entry_id, result)





    def cycle(self):

        """执行一个周期"""

        self.cycles += 1

        # 尝试提交

        while self.rob.commit_ready():

            entry = self.rob.commit()

            if entry is not None:

                pass  # 提交处理





def basic_test():

    """基本功能测试"""

    print("=== ROB模拟器测试 ===")

    proc = ROB_Processor(rob_size=16)

    print(f"ROB容量: {proc.rob.size}")

    # 发射一些指令

    print("\n发射指令序列:")

    instrs = [

        (Instruction_Type.ALU, 1),

        (Instruction_Type.ALU, 2),

        (Instruction_Type.LOAD, 3),

        (Instruction_Type.ALU, 1),

        (Instruction_Type.STORE, None),

    ]

    issued_ids = []

    for i, (instr_type, dest) in enumerate(instrs):

        entry_id = proc.issue_instruction(instr_type, dest)

        issued_ids.append(entry_id)

        print(f"  指令{i}: type={instr_type.name}, dest=r{dest}, rob_id={entry_id}")

    # 模拟执行完成

    print("\n执行完成:")

    for i, entry_id in enumerate(issued_ids):

        if entry_id is not None:

            result = random.randint(1, 100)

            proc.execute_instruction(entry_id, result)

            print(f"  rob_id={entry_id}: result={result}")

    # 提交

    print("\n提交:")

    for _ in range(len(issued_ids)):

        entry = proc.rob.commit()

        if entry:

            print(f"  提交 rob_id={entry.id}, pc=0x{entry.instruction_pc:x}, dest={entry.dest_logical_reg}")

    print(f"\n统计:")

    print(f"  总周期: {proc.cycles}")

    print(f"  总指令: {proc.total_instructions}")

    print(f"  已提交: {proc.rob.committed_count}")

    print(f"  已squash: {proc.rob.squashed_count}")





if __name__ == "__main__":

    basic_test()

