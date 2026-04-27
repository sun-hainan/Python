# -*- coding: utf-8 -*-

"""

算法实现：计算机体系结构_2 / superscalar_ooo



本文件实现 superscalar_ooo 相关的算法功能。

"""



import random

from typing import List, Dict, Optional, Tuple

from dataclasses import dataclass, field

from enum import Enum, auto





class Opcode(Enum):

    """指令操作码枚举"""

    ADD = auto()      # 加法

    SUB = auto()     # 减法

    MUL = auto()     # 乘法

    LOAD = auto()    # 内存加载

    STORE = auto()   # 内存存储

    BRANCH = auto()  # 条件分支

    NOP = auto()     # 空操作





class FU_Type(Enum):

    """功能单元类型"""

    ALU = auto()     # 算术逻辑单元（可发射ADD/SUB/MUL）

    LSU = auto()     # 加载存储单元（LOAD/STORE）

    BRU = auto()     # 分支单元





@dataclass

class Instruction:

    """指令描述符"""

    id: int                    # 指令唯一标识

    opcode: Opcode             # 操作码

    dest: Optional[int]        # 目标寄存器（物理寄存器号）

    src1: Optional[int]        # 源操作数1（物理寄存器号）

    src2: Optional[int]        # 源操作数2（物理寄存器号）

    ready: bool = False        # 操作数就绪标志

    executing: bool = False    # 正在执行标志

    completed: bool = False    # 执行完成标志

    pc: int = 0                # 程序计数器





@dataclass

class Register_File:

    """寄存器文件"""

    # 逻辑寄存器到物理寄存器的映射表

    map_table: Dict[int, int] = field(default_factory=dict)

    # 物理寄存器是否空闲

    free_list: List[bool] = field(default_factory=lambda: [True] * 32)

    # 物理寄存器当前值

    values: List[Optional[int]] = field(default_factory=lambda: [None] * 32)

    # 逻辑寄存器总数

    num_logical: int = 16





class Reorder_Buffer:

    """重排序缓冲（ROB）"""

    def __init__(self, size: int = 16):

        self.size = size                    # ROB容量

        self.buffer: List[Optional[Instruction]] = [None] * size

        self.head: int = 0                  # 最早提交指令位置

        self.tail: int = 0                  # 最新进入指令位置

        self.count: int = 0                 # 当前条目数





    def is_full(self) -> bool:

        """判断ROB是否已满"""

        return self.count >= self.size





    def is_empty(self) -> bool:

        """判断ROB是否为空"""

        return self.count == 0





    def enqueue(self, instr: Instruction) -> bool:

        """将指令加入ROB尾部"""

        if self.is_full():

            return False

        self.buffer[self.tail] = instr

        self.tail = (self.tail + 1) % self.size

        self.count += 1

        return True





    def dequeue(self) -> Optional[Instruction]:

        """从ROB头部取出最早指令并提交"""

        if self.is_empty():

            return None

        instr = self.buffer[self.head]

        self.buffer[self.head] = None

        self.head = (self.head + 1) % self.size

        self.count -= 1

        return instr





class Reservation_Station:

    """预约站（Reservation Station）"""

    def __init__(self, fu_type: FU_Type, size: int = 8):

        self.fu_type = fu_type              # 功能单元类型

        self.size = size                    # 预约站容量

        self.entries: List[Optional[Instruction]] = [None] * size

        self.count: int = 0                 # 当前条目数





    def is_full(self) -> bool:

        """判断预约站是否已满"""

        return self.count >= self.size





    def is_empty(self) -> bool:

        """判断预约站是否为空"""

        return self.count == 0





    def insert(self, instr: Instruction) -> bool:

        """插入指令到预约站"""

        if self.is_full():

            return False

        for i in range(self.size):

            if self.entries[i] is None:

                self.entries[i] = instr

                self.count += 1

                return True

        return False





    def dispatch(self) -> Optional[Instruction]:

        """调度一条就绪指令（乱序）"""

        for i in range(self.size):

            instr = self.entries[i]

            if instr is not None and instr.ready and not instr.executing:

                instr.executing = True

                return instr

        return None





class Superscalar_CPU:

    """超标量乱序执行处理器模型"""

    def __init__(self, width: int = 4, rob_size: int = 16):

        self.width = width                  # 发射宽度（每周期可发射指令数）

        # 预约站：2个ALU、1个LSU、1个BRU

        self.rs_alu1 = Reservation_Station(FU_Type.ALU, size=8)

        self.rs_alu2 = Reservation_Station(FU_Type.ALU, size=8)

        self.rs_lsu = Reservation_Station(FU_Type.LSU, size=8)

        self.rs_bru = Reservation_Station(FU_Type.BRU, size=8)

        # 寄存器文件

        self.reg_file = Register_File()

        # 重排序缓冲

        self.rob = Reorder_Buffer(size=rob_size)

        # 当前周期数

        self.cycle: int = 0

        # 已提交指令计数

        self.committed: int = 0

        # 运行标志

        self.running: bool = False

        # 待发射指令队列

        self.fetch_queue: List[Instruction] = []

        self.next_instr_id: int = 0





    def fetch_instruction(self) -> Instruction:

        """模拟取指阶段：生成随机指令"""

        opcodes = [Opcode.ADD, Opcode.SUB, Opcode.MUL, Opcode.LOAD, Opcode.STORE, Opcode.BRANCH]

        opcode = random.choice(opcodes)

        dest = random.randint(0, 15) if opcode != Opcode.STORE and opcode != Opcode.BRANCH else None

        src1 = random.randint(0, 15)

        src2 = random.randint(0, 15) if opcode not in [Opcode.LOAD, Opcode.BRANCH] else None

        instr = Instruction(

            id=self.next_instr_id,

            opcode=opcode,

            dest=dest,

            src1=src1,

            src2=src2,

            pc=self.next_instr_id * 4

        )

        self.next_instr_id += 1

        return instr





    def issue(self, instr: Instruction) -> bool:

        """发射阶段：为指令分配ROB条目和物理寄存器，重命名寄存器"""

        if self.rob.is_full():

            return False

        # 分配新的物理寄存器作为目标

        new_dest = self._alloc_physical_reg()

        if new_dest is None:

            return False

        # 更新映射表（旧映射入ROB用于恢复）

        if instr.dest is not None:

            old_map = self.reg_file.map_table.get(instr.dest)

            self.reg_file.map_table[instr.dest] = new_dest

            instr.dest = new_dest

        # 将指令加入ROB

        self.rob.enqueue(instr)

        # 插入对应预约站

        rs = self._select_rs(instr.opcode)

        if rs is None or rs.is_full():

            return False

        rs.insert(instr)

        return True





    def _alloc_physical_reg(self) -> Optional[int]:

        """从空闲列表分配一个物理寄存器"""

        for i in range(len(self.reg_file.free_list)):

            if self.reg_file.free_list[i]:

                self.reg_file.free_list[i] = False

                return i

        return None





    def _select_rs(self, opcode: Opcode) -> Optional[Reservation_Station]:

        """根据操作码选择对应的预约站"""

        if opcode == Opcode.LOAD or opcode == Opcode.STORE:

            return self.rs_lsu

        elif opcode == Opcode.BRANCH:

            return self.rs_bru

        else:  # ADD/SUB/MUL

            return self.rs_alu1 if self.rs_alu1.count <= self.rs_alu2.count else self.rs_alu2





    def execute_step(self):

        """执行一个周期：调度就绪指令→执行→更新状态"""

        self.cycle += 1

        # 调度所有预约站中的就绪指令

        for rs in [self.rs_alu1, self.rs_alu2, self.rs_lsu, self.rs_bru]:

            while True:

                instr = rs.dispatch()

                if instr is None:

                    break

                # 模拟执行延迟

                instr.completed = True

        # 检查ROB头部指令是否可以提交

        while not self.rob.is_empty():

            head_instr = self.rob.buffer[self.rob.head]

            if head_instr is not None and head_instr.completed:

                # 提交指令，释放物理寄存器

                self.rob.dequeue()

                self.committed += 1

            else:

                break





    def run(self, num_cycles: int = 100, verbose: bool = False):

        """运行处理器模拟指定周期数"""

        self.running = True

        for cycle in range(num_cycles):

            # 取指阶段：每周期取width条指令

            for _ in range(self.width):

                instr = self.fetch_instruction()

                self.issue(instr)

            # 执行一个周期

            self.execute_step()

            if verbose and cycle % 20 == 0:

                print(f"Cycle {self.cycle}: Committed {self.committed} instructions")





def basic_test():

    """基本功能测试"""

    cpu = Superscalar_CPU(width=4, rob_size=32)

    print("=== 超标量乱序执行模拟器测试 ===")

    print(f"发射宽度: {cpu.width}, ROB容量: {cpu.rob.size}")

    # 运行50个周期

    cpu.run(num_cycles=50, verbose=True)

    print(f"\n最终统计:")

    print(f"  总周期数: {cpu.cycle}")

    print(f"  已提交指令数: {cpu.committed}")

    print(f"  IPC: {cpu.committed / cpu.cycle:.2f}")

    print(f"  ALU1预约站占用: {cpu.rs_alu1.count}/{cpu.rs_alu1.size}")

    print(f"  LSU预约站占用: {cpu.rs_lsu.count}/{cpu.rs_lsu.size}")





if __name__ == "__main__":

    basic_test()

