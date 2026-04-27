# -*- coding: utf-8 -*-

"""

算法实现：计算机体系结构_2 / out_of_order_retire



本文件实现 out_of_order_retire 相关的算法功能。

"""



import random

from typing import List, Optional, Dict, Set, Tuple

from dataclasses import dataclass, field

from enum import Enum, auto





class Retire_State(Enum):

    """退役单元状态"""

    IDLE = auto()

    RETIRING = auto()

    STALLED = auto()





class Instruction_Status(Enum):

    """指令状态"""

    PENDING = auto()

    EXECUTING = auto()

    COMPLETED = auto()

    SQUASHED = auto()

    COMMITTED = auto()





@dataclass

class Retire_Entry:

    """退役条目"""

    id: int = 0

    pc: int = 0

    dest_phys_reg: Optional[int] = None

    dest_logical_reg: Optional[int] = None

    result_value: Optional[int] = None

    exception: bool = False

    mispredicted: bool = False

    target_pc: int = 0

    status: Instruction_Status = Instruction_Status.PENDING

    age: int = 0  # 程序顺序





class Register_File:

    """寄存器文件"""

    def __init__(self, num_phys: int = 64, num_logical: int = 16):

        self.num_phys = num_phys

        self.num_logical = num_logical

        self.values: List[Optional[int]] = [None] * num_phys

        self.valid: List[bool] = [False] * num_phys

        self.map_table: Dict[int, int] = {i: i for i in range(num_logical)}





    def write(self, phys_reg: int, value: int):

        """写入物理寄存器"""

        if 0 <= phys_reg < self.num_phys:

            self.values[phys_reg] = value

            self.valid[phys_reg] = True





    def read(self, phys_reg: int) -> Optional[int]:

        """读取物理寄存器"""

        if 0 <= phys_reg < self.num_phys and self.valid[phys_reg]:

            return self.values[phys_reg]

        return None





class Retire_Unit:

    """退役单元"""

    def __init__(self, width: int = 4, rob_size: int = 32):

        self.width = width                        # 每周期最多退役指令数

        self.rob_size = rob_size

        # ROB

        self.rob: List[Optional[Retire_Entry]] = [None] * rob_size

        self.head: int = 0

        self.tail: int = 0

        self.count: int = 0

        self.next_id: int = 0

        # 寄存器文件

        self.reg_file = Register_File()

        # 状态

        self.state = Retire_State.IDLE

        # 统计

        self.committed_count: int = 0

        self.squashed_count: int = 0

        self.exception_count: int = 0





    def is_full(self) -> bool:

        """ROB是否已满"""

        return self.count >= self.rob_size





    def is_empty(self) -> bool:

        """ROB是否为空"""

        return self.count == 0





    def _advance(self, idx: int) -> int:

        """环形索引前进"""

        return (idx + 1) % self.rob_size





    def allocate(self, pc: int, dest_logical: Optional[int] = None) -> Optional[int]:

        """分配ROB条目"""

        if self.is_full():

            return None

        entry_id = self.next_id

        self.next_id += 1

        entry = Retire_Entry(id=entry_id, pc=pc, dest_logical_reg=dest_logical, age=self.count)

        # 寄存器重命名

        if dest_logical is not None:

            old_phys = self.reg_file.map_table.get(dest_logical)

            # 分配新物理寄存器

            for i in range(self.num_logical(), self.reg_file.num_phys):

                if not self.reg_file.valid[i]:

                    self.reg_file.map_table[dest_logical] = i

                    entry.dest_phys_reg = i

                    break

        self.rob[self.tail] = entry

        self.tail = self._advance(self.tail)

        self.count += 1

        return entry_id





    def num_logical(self) -> int:

        return self.reg_file.num_logical





    def complete(self, entry_id: int, result_value: int):

        """标记指令为完成状态"""

        for i in range(self.rob_size):

            entry = self.rob[i]

            if entry is not None and entry.id == entry_id:

                entry.result_value = result_value

                entry.status = Instruction_Status.COMPLETED

                # 写入寄存器文件

                if entry.dest_phys_reg is not None:

                    self.reg_file.write(entry.dest_phys_reg, result_value)

                break





    def squash(self, entry_id: int):

        """Squash从entry_id开始的所有条目"""

        idx = self.head

        squashed = 0

        while idx != self.tail:

            entry = self.rob[idx]

            if entry is not None and entry.id >= entry_id:

                entry.status = Instruction_Status.SQUASHED

                squashed += 1

            idx = self._advance(idx)

        self.squashed_count += squashed





    def squash_after_rob_id(self, rob_id: int):

        """Squash所有 rob_id 之后的条目"""

        idx = self.head

        squashed = 0

        while idx != self.tail:

            entry = self.rob[idx]

            if entry is not None and entry.age > rob_id:

                entry.status = Instruction_Status.SQUASHED

                squashed += 1

            idx = self._advance(idx)

        self.squashed_count += squashed





    def retire(self) -> List[Retire_Entry]:

        """退役已完成的指令（按顺序）"""

        retired = []

        for _ in range(self.width):

            if self.is_empty():

                break

            entry = self.rob[self.head]

            if entry is None:

                break

            # 检查是否准备好退役

            if entry.status == Instruction_Status.COMPLETED:

                # 检查异常

                if entry.exception:

                    self.exception_count += 1

                    # 精确中断：squash所有后续指令

                    self.squash_after_rob_id(entry.age)

                    break

                # 退役

                entry.status = Instruction_Status.COMMITTED

                self.rob[self.head] = None

                self.head = self._advance(self.head)

                self.count -= 1

                self.committed_count += 1

                retired.append(entry)

            elif entry.status == Instruction_Status.SQUASHED:

                # 跳过已squash的条目

                self.rob[self.head] = None

                self.head = self._advance(self.head)

                self.count -= 1

            else:

                # 指令未完成，需要等待

                break

        return retired





    def get_head_ready(self) -> bool:

        """检查头部指令是否准备好退役"""

        if self.is_empty():

            return False

        entry = self.rob[self.head]

        return entry is not None and entry.status == Instruction_Status.COMPLETED





class Retire_Simulator:

    """退役单元模拟器"""

    def __init__(self, width: int = 4):

        self.retire_unit = Retire_Unit(width=width)

        self.cycles: int = 0

        self.total_instructions: int = 0





    def issue_instruction(self, pc: int, dest_logical: Optional[int] = None) -> Optional[int]:

        """发射指令"""

        entry_id = self.retire_unit.allocate(pc, dest_logical)

        if entry_id is not None:

            self.total_instructions += 1

        return entry_id





    def complete_instruction(self, entry_id: int, result: int = 0):

        """完成指令"""

        self.retire_unit.complete(entry_id, result)





    def run_cycle(self) -> int:

        """运行一个周期，返回退役指令数"""

        self.cycles += 1

        retired = self.retire_unit.retire()

        return len(retired)





def basic_test():

    """基本功能测试"""

    print("=== 乱序退役单元测试 ===")

    sim = Retire_Simulator(width=4)

    print(f"退役宽度: {sim.retire_unit.width}")

    print(f"ROB容量: {sim.retire_unit.rob_size}")

    # 发射一些指令

    print("\n发射指令:")

    issued_ids = []

    for i in range(8):

        entry_id = sim.issue_instruction(pc=0x1000 + i * 4, dest_logical=i % 16)

        issued_ids.append(entry_id)

        print(f"  指令{i}: entry_id={entry_id}, dest=r{i % 16}")

    # 完成部分指令

    print("\n完成指令:")

    for i, entry_id in enumerate(issued_ids[:6]):

        if entry_id is not None:

            sim.complete_instruction(entry_id, result=random.randint(1, 100))

            print(f"  entry_id={entry_id}: completed")

    # 退役

    print("\n退役周期:")

    for cycle in range(5):

        retired_count = sim.run_cycle()

        print(f"  Cycle {sim.cycles}: 退役 {retired_count} 条指令, 总计已退役 {sim.retire_unit.committed_count}")

        if retired_count == 0 and not sim.retire_unit.get_head_ready():

            break

    # 测试squash

    print("\n测试异常处理（squash）:")

    # 发射更多指令

    for i in range(8, 12):

        entry_id = sim.issue_instruction(pc=0x1000 + i * 4, dest_logical=i % 16)

        if entry_id is not None:

            sim.complete_instruction(entry_id, result=random.randint(1, 100))

    # 模拟在entry_id=10处发生异常

    print("  模拟在entry_id=10处发生异常，squash后续指令")

    sim.retire_unit.squash_after_rob_id(10)

    # 再运行几个周期

    for cycle in range(3):

        retired_count = sim.run_cycle()

        print(f"  Cycle {sim.cycles}: 退役 {retired_count} 条指令")

    print(f"\n最终统计:")

    print(f"  总周期: {sim.cycles}")

    print(f"  总指令: {sim.total_instructions}")

    print(f"  已退役: {sim.retire_unit.committed_count}")

    print(f"  已squash: {sim.retire_unit.squashed_count}")

    print(f"  异常次数: {sim.retire_unit.exception_count}")





if __name__ == "__main__":

    basic_test()

