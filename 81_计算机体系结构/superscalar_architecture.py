# -*- coding: utf-8 -*-

"""

算法实现：计算机体系结构 / superscalar_architecture



本文件实现 superscalar_architecture 相关的算法功能。

"""



from typing import List, Dict, Optional, Tuple

from dataclasses import dataclass

from enum import Enum

import copy





class InstructionType(Enum):

    """指令类型"""

    ALU = "ALU"

    LOAD = "LOAD"

    STORE = "STORE"

    BRANCH = "BRANCH"





@dataclass

class Instruction:

    """超标量指令"""

    id: int

    type: InstructionType

    dest: int = -1          # 目的寄存器

    src1: int = -1          # 源寄存器1

    src2: int = -1          # 源寄存器2

    immediate: int = 0      # 立即数



    # 执行状态

    issued: bool = False

    executing: bool = False

    completed: bool = False

    committed: bool = False



    # 资源分配

    alu_unit: Optional[int] = None

    rob_entry: Optional[int] = None



    # 执行信息

    latency: int = 1         # 执行延迟

    remaining_cycles: int = 0  # 剩余周期





class ReorderBuffer:

    """重排序缓冲区 (ROB)"""



    def __init__(self, size: int = 16):

        self.size = size

        self.entries: List[Optional[Instruction]] = [None] * size

        self.head: int = 0

        self.tail: int = 0

        self.count: int = 0



    def is_full(self) -> bool:

        return self.count >= self.size



    def is_empty(self) -> bool:

        return self.count == 0



    def allocate(self, instr: Instruction) -> Optional[int]:

        """分配ROB条目"""

        if self.is_full():

            return None



        entry_id = self.tail

        self.entries[entry_id] = copy.deepcopy(instr)

        self.entries[entry_id].rob_entry = entry_id

        self.tail = (self.tail + 1) % self.size

        self.count += 1

        return entry_id



    def get_head(self) -> Optional[Instruction]:

        """获取头部条目（最早发射的）"""

        if self.is_empty():

            return None

        return self.entries[self.head]



    def commit(self) -> Optional[Instruction]:

        """退役头部条目"""

        if self.is_empty():

            return None



        head_entry = self.entries[self.head]

        if head_entry and head_entry.completed:

            self.entries[self.head] = None

            self.head = (self.head + 1) % self.size

            self.count -= 1

            return head_entry

        return None





class RegisterFile:

    """超标量寄存器文件"""



    def __init__(self, num_regs: int = 32):

        self.num_regs = num_regs

        self.values: List[int] = [0] * num_regs

        # 每个寄存器的ROB条目（寄存器重命名）

        self.pending_rob: List[Optional[int]] = [None] * num_regs



    def read(self, reg: int) -> int:

        """读取寄存器值"""

        return self.values[reg]



    def write(self, reg: int, value: int):

        """写寄存器"""

        self.values[reg] = value

        self.pending_rob[reg] = None



    def is_ready(self, reg: int) -> bool:

        """寄存器是否就绪"""

        return self.pending_rob[reg] is None





class ALUUnit:

    """ALU执行单元"""



    def __init__(self, unit_id: int, latency: int = 1):

        self.unit_id = unit_id

        self.latency = latency

        self.busy: bool = False

        self.current_instr: Optional[Instruction] = None

        self.remaining: int = 0



    def issue(self, instr: Instruction):

        """发射指令"""

        self.busy = True

        self.current_instr = copy.deepcopy(instr)

        self.current_instr.alu_unit = self.unit_id

        self.remaining = self.latency



    def tick(self) -> Optional[Instruction]:

        """执行一个周期，返回完成的指令"""

        if not self.busy:

            return None



        self.remaining -= 1

        if self.remaining <= 0:

            self.busy = False

            completed = self.current_instr

            self.current_instr = None

            return completed

        return None





class LoadStoreUnit:

    """Load/Store单元"""



    def __init__(self, unit_id: int, latency: int = 2):

        self.unit_id = unit_id

        self.latency = latency

        self.busy: bool = False

        self.current_instr: Optional[Instruction] = None

        self.remaining: int = 0



    def issue(self, instr: Instruction):

        """发射指令"""

        self.busy = True

        self.current_instr = copy.deepcopy(instr)

        self.remaining = self.latency



    def tick(self) -> Optional[Instruction]:

        """执行一个周期"""

        if not self.busy:

            return None



        self.remaining -= 1

        if self.remaining <= 0:

            self.busy = False

            completed = self.current_instr

            self.current_instr = None

            return completed

        return None





class SuperscalarCore:

    """

    超标量处理器核



    参数：

    - issue_width: 发射宽度

    - num_alu: ALU数量

    - num_ls: Load/Store单元数量

    - rob_size: ROB大小

    """



    def __init__(self, issue_width: int = 4, num_alu: int = 2, num_ls: int = 1, rob_size: int = 16):

        self.issue_width = issue_width



        # 资源

        self.registers = RegisterFile(num_regs=32)

        self.rob = ReorderBuffer(size=rob_size)



        # 执行单元

        self.alu_units: List[ALUUnit] = [

            ALUUnit(i, latency=1) for i in range(num_alu)

        ]

        self.ls_unit = LoadStoreUnit(0, latency=2)



        # 内存（模拟）

        self.memory: Dict[int, int] = {}



        # 指令队列

        self.instruction_queue: List[Instruction] = []



        # 已完成指令

        self.completed: List[Instruction] = []



        # 时钟

        self.cycle: int = 0



        # 统计

        self.total_issued: int = 0

        self.total_committed: int = 0



    def load_instructions(self, instructions: List[Instruction]):

        """加载指令到队列"""

        self.instruction_queue = copy.deepcopy(instructions)



    def _get_ready_instructions(self) -> List[Instruction]:

        """获取所有就绪指令（依赖已满足）"""

        ready = []

        for instr in self.instruction_queue:

            if instr.issued:

                continue



            # 检查源操作数是否就绪

            src1_ready = (instr.src1 < 0) or self.registers.is_ready(instr.src1)

            src2_ready = (instr.src2 < 0) or self.registers.is_ready(instr.src2)



            if src1_ready and src2_ready:

                ready.append(instr)



        return ready



    def _can_dispatch(self) -> bool:

        """检查是否可以分发（ROB未满且有可用执行单元）"""

        if self.rob.is_full():

            return False



        # 检查执行单元可用性

        if self.instruction_queue and not self.instruction_queue[0].issued:

            return True

        return False



    def _issue_instructions(self):

        """发射阶段：选择最多issue_width条指令发射"""

        issued = 0

        ready = self._get_ready_instructions()



        # 按类型分组

        alu_instrs = [i for i in ready if i.type == InstructionType.ALU]

        ls_instrs = [i for i in ready if i.type in (InstructionType.LOAD, InstructionType.STORE)]



        # 分配执行单元

        for instr in alu_instrs:

            if issued >= self.issue_width:

                break



            # 找空闲ALU

            for alu in self.alu_units:

                if not alu.busy:

                    # 分配ROB条目

                    rob_id = self.rob.allocate(instr)

                    if rob_id is not None:

                        instr.rob_entry = rob_id

                        instr.issued = True

                        instr.remaining_cycles = instr.latency

                        alu.issue(instr)

                        issued += 1

                    break



        for instr in ls_instrs:

            if issued >= self.issue_width:

                break



            if not self.ls_unit.busy:

                rob_id = self.rob.allocate(instr)

                if rob_id is not None:

                    instr.rob_entry = rob_id

                    instr.issued = True

                    instr.remaining_cycles = instr.latency

                    self.ls_unit.issue(instr)

                    issued += 1



        self.total_issued += issued



    def _execute_instructions(self):

        """执行阶段"""

        # ALU执行

        for alu in self.alu_units:

            completed = alu.tick()

            if completed:

                completed.completed = True

                # 标记ROB条目完成

                if completed.rob_entry is not None:

                    self.completed.append(completed)



        # Load/Store执行

        completed = self.ls_unit.tick()

        if completed:

            completed.completed = True

            if completed.rob_entry is not None:

                self.completed.append(completed)



    def _commit_instructions(self):

        """退役阶段：按顺序退役完成的指令"""

        while True:

            head = self.rob.get_head()

            if head is None or not head.completed:

                break



            committed = self.rob.commit()

            if committed:

                committed.committed = True

                self.total_committed += 1



                # 写回结果到寄存器

                if committed.dest >= 0:

                    if committed.type == InstructionType.ALU:

                        v1 = self.registers.read(committed.src1) if committed.src1 >= 0 else 0

                        v2 = self.registers.read(committed.src2) if committed.src2 >= 0 else 0

                        if committed.type == InstructionType.ALU:

                            result = v1 + v2  # 简化

                    elif committed.type == InstructionType.LOAD:

                        result = self.memory.get(committed.immediate, 0)

                    else:

                        result = 0

                    self.registers.write(committed.dest, result)



    def step(self) -> List[str]:

        """执行一个时钟周期"""

        self.cycle += 1

        actions = []



        # 1. 退役

        committed = self.rob.commit()

        while committed:

            committed.committed = True

            self.total_committed += 1

            actions.append(f"退役I{committed.id}")

            committed = self.rob.commit()



        # 2. 执行

        for alu in self.alu_units:

            if alu.tick():

                actions.append(f"ALU{alu.unit_id}完成")

        if self.ls_unit.tick():

            actions.append("LS完成")



        # 3. 发射

        self._issue_instructions()



        return actions



    def run(self, max_cycles: int = 100) -> Dict:

        """运行模拟"""

        print(f"\n开始模拟 (发射宽度={self.issue_width})")

        print("-" * 50)



        while self.total_committed < len(self.instruction_queue) and self.cycle < max_cycles:

            actions = self.step()

            if actions:

                print(f"Cycle {self.cycle:2d}: {', '.join(actions)}")



        return {

            'total_cycles': self.cycle,

            'total_issued': self.total_issued,

            'total_committed': self.total_committed,

            'ipc': self.total_committed / self.cycle if self.cycle > 0 else 0

        }





def simulate_superscalar():

    """

    模拟超标量处理器

    """

    print("=" * 60)

    print("超标量架构 (Superscalar) 模拟")

    print("=" * 60)



    # 创建4发射宽度的超标量核

    core = SuperscalarCore(issue_width=4, num_alu=2, num_ls=1, rob_size=16)



    # 初始化寄存器

    for i in range(1, 8):

        core.registers.write(i, i * 10)



    # 创建指令序列

    instructions = [

        # 初始设置

        Instruction(1, InstructionType.LOAD, dest=1, immediate=0x100),

        Instruction(2, InstructionType.LOAD, dest=2, immediate=0x200),

        # 计算指令

        Instruction(3, InstructionType.ALU, dest=3, src1=1, src2=2),

        Instruction(4, InstructionType.ALU, dest=4, src1=2, src2=3),

        Instruction(5, InstructionType.ALU, dest=5, src1=3, src2=4),

        # 更多计算

        Instruction(6, InstructionType.ALU, dest=6, src1=1, src2=5),

        Instruction(7, InstructionType.ALU, dest=7, src1=4, src2=6),

        Instruction(8, InstructionType.ALU, dest=8, src1=5, src2=7),

    ]



    for instr in instructions:

        instr.latency = 1 if instr.type == InstructionType.ALU else 2



    core.load_instructions(instructions)



    print("\n指令序列:")

    for instr in instructions:

        if instr.type == InstructionType.LOAD:

            print(f"  I{instr.id}: {instr.type.value} R{instr.dest}, [0x{instr.immediate:X}]")

        else:

            print(f"  I{instr.id}: {instr.type.value} R{instr.dest} = R{instr.src1} + R{instr.src2}")



    # 运行模拟

    stats = core.run(max_cycles=50)



    print("\n" + "=" * 60)

    print("执行结果:")

    print("=" * 60)

    print(f"  总周期数: {stats['total_cycles']}")

    print(f"  总发射指令数: {stats['total_issued']}")

    print(f"  总退役指令数: {stats['total_committed']}")

    print(f"  IPC (Instructions Per Cycle): {stats['ipc']:.2f}")

    print(f"  发射宽度利用率: {stats['total_issued'] / stats['total_cycles'] / core.issue_width * 100:.1f}%")





if __name__ == "__main__":

    simulate_superscalar()

