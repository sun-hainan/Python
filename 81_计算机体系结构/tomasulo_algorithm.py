# -*- coding: utf-8 -*-

"""

算法实现：计算机体系结构 / tomasulo_algorithm



本文件实现 tomasulo_algorithm 相关的算法功能。

"""



from enum import Enum

from typing import List, Optional, Dict

from dataclasses import dataclass, field





class OpType(Enum):

    """指令操作类型"""

    ADD = "ADD"      # 加法

    SUB = "SUB"      # 减法

    MUL = "MUL"      # 乘法

    DIV = "DIV"      # 除法

    LOAD = "LOAD"    # 加载

    STORE = "STORE"  # 存储





class InstructionState(Enum):

    """指令状态"""

    ISSUE = "ISSUE"          # 发射

    EXECUTE = "EXECUTE"      # 执行

    WRITE_RESULT = "WRITE_RESULT"  # 写回

    COMMIT = "COMMIT"        # 退役





@dataclass

class Instruction:

    """指令描述"""

    id: int               # 指令序号

    op: OpType            # 操作类型

    dest: int             # 目标寄存器号

    src1: int             # 源操作数1寄存器号

    src2: int             # 源操作数2寄存器号

    immediate: int = 0    # 立即数（用于LOAD/STORE地址偏移）

    state: InstructionState = InstructionState.ISSUE

    remaining_cycles: int = 0  # 剩余执行周期





@dataclass

class ReservationStationEntry:

    """保留站条目"""

    busy: bool = False              # 是否忙

    op: Optional[OpType] = None     # 操作类型

    vj: Optional[float] = None      # 源操作数1的值

    vk: Optional[float] = None      # 源操作数2的值

    qj: Optional[int] = None        # 源操作数1对应的保留站号（未就绪）

    qk: Optional[int] = None        # 源操作数2对应的保留站号（未就绪）

    dest: int = -1                  # 目标寄存器号

    imm: int = 0                    # 立即数





@dataclass

class ROBEntry:

    """重排序缓冲区(ROB)条目"""

    in_use: bool = False           # 是否在用

    instruction: Optional[Instruction] = None

    value: Optional[float] = None   # 执行结果

    ready: bool = False            # 结果是否就绪





class RegisterFile:

    """寄存器文件"""



    def __init__(self, num_regs=32):

        """

        初始化寄存器文件

        param num_regs: 寄存器数量

        """

        self.num_regs = num_regs

        # 寄存器值

        self.values = [0.0] * num_regs

        # 寄存器状态：哪个ROB条目正在写入此寄存器（寄存器重命名）

        # None表示寄存器有有效值

        self.rob_tag = [None] * num_regs



    def read(self, reg: int) -> float:

        """读取寄存器值"""

        return self.values[reg]



    def write(self, reg: int, value: float):

        """写入寄存器"""

        self.values[reg] = value

        self.rob_tag[reg] = None



    def set_pending(self, reg: int, rob_tag: int):

        """设置寄存器pending状态（等待ROB结果）"""

        self.rob_tag[reg] = rob_tag



    def is_pending(self, reg: int) -> bool:

        """检查寄存器是否pending"""

        return self.rob_tag[reg] is not None





class TomasuloSimulator:

    """

    Tomasulo算法模拟器



    支持：

    - 寄存器重命名

    - 乱序发射

    - 乱序执行

    - 乱序完成，顺序退役

    """



    def __init__(self, num_reservation_stations=5, num_rob_entries=10, num_registers=32):

        """

        初始化模拟器

        param num_reservation_stations: 保留站数量

        param num_rob_entries: ROB条目数量

        param num_registers: 寄存器数量

        """

        self.num_rs = num_reservation_stations

        self.num_rob = num_rob_entries

        self.registers = RegisterFile(num_registers)



        # 保留站

        self.reservation_stations = [

            ReservationStationEntry() for _ in range(num_reservation_stations)

        ]



        # 重排序缓冲区

        self.rob = [ROBEntry() for _ in range(num_rob_entries)]

        self.rob_head = 0  # 退役指针

        self.rob_tail = 0  # 添加指针



        # 功能单元延迟（周期数）

        self.latency = {

            OpType.ADD: 1,

            OpType.SUB: 1,

            OpType.MUL: 3,

            OpType.DIV: 6,

            OpType.LOAD: 2,

            OpType.STORE: 1,

        }



        # 当前正在执行的指令

        self.executing = []  # 正在执行的保留站索引

        # 已完成的待写回指令

        self.completed = []  # (保留站索引, 结果值)



        # 时钟周期

        self.cycle = 0



        # 统计

        self.total_instructions = 0



    def _find_free_rob(self) -> Optional[int]:

        """找一个空闲的ROB条目"""

        for i in range(self.num_rob):

            if not self.rob[i].in_use:

                return i

        return None



    def _find_free_rs(self) -> Optional[int]:

        """找一个空闲的保留站"""

        for i in range(self.num_rs):

            if not self.reservation_stations[i].busy:

                return i

        return None



    def _get_rob_value(self, rob_tag: int) -> Optional[float]:

        """从ROB获取值（如果就绪）"""

        if rob_tag is None:

            return None

        entry = self.rob[rob_tag]

        if entry.ready:

            return entry.value

        return None



    def issue(self, instr: Instruction) -> bool:

        """

        发射指令到保留站

        param instr: 指令

        return: 是否成功发射

        """

        rs_index = self._find_free_rs()

        rob_index = self._find_free_rob()



        if rs_index is None or rob_index is None:

            return False  # 保留站或ROB满



        # 获取保留站条目

        rs = self.reservation_stations[rs_index]



        # 检查源操作数是否就绪

        # 源操作数1

        if self.registers.is_pending(instr.src1):

            # 寄存器pending，依赖某个ROB

            rs.qj = self.registers.rob_tag[instr.src1]

            rs.vj = None

        else:

            rs.vj = self.registers.read(instr.src1)

            rs.qj = None



        # 源操作数2

        if self.registers.is_pending(instr.src2):

            rs.qk = self.registers.rob_tag[instr.src2]

            rs.vk = None

        else:

            rs.vk = self.registers.read(instr.src2)

            rs.qk = None



        # 设置保留站

        rs.busy = True

        rs.op = instr.op

        rs.dest = instr.dest

        rs.imm = instr.immediate



        # 分配ROB条目，设置寄存器重命名

        self.rob[rob_index].in_use = True

        self.rob[rob_index].instruction = instr

        self.rob[rob_index].ready = False

        self.rob[rob_index].value = None



        # 寄存器重命名：目标寄存器指向此ROB条目

        self.registers.set_pending(instr.dest, rob_index)



        # 设置指令信息

        instr.state = InstructionState.ISSUE

        instr.remaining_cycles = self.latency[instr.op]



        self.total_instructions += 1

        return True



    def _execute_ready_instructions(self):

        """执行已就绪的指令"""

        for i in range(self.num_rs):

            rs = self.reservation_stations[i]

            if not rs.busy:

                continue



            # 检查两个源操作数是否都就绪

            src1_ready = (rs.vj is not None) and (rs.qj is None)

            src2_ready = (rs.vk is not None) and (rs.qk is None)



            if src1_ready and src2_ready and i not in self.executing:

                # 指令就绪，开始执行

                self.executing.append(i)



    def _execute_instructions(self):

        """执行正在执行的指令（减少剩余周期）"""

        still_executing = []

        for i in self.executing:

            rs = self.reservation_stations[i]

            rs.dest  # 保持引用

            self.rob  # 保持引用



            # 减少剩余周期

            if hasattr(rs, 'remaining_cycles'):

                rs.remaining_cycles -= 1



            # 检查CDB上是否有需要的值

            if rs.qj is not None:

                val = self._get_rob_value(rs.qj)

                if val is not None:

                    rs.vj = val

                    rs.qj = None

            if rs.qk is not None:

                val = self._get_rob_value(rs.qk)

                if val is not None:

                    rs.vk = val

                    rs.qk = None



            still_executing.append(i)



        self.executing = still_executing



    def _write_result(self):

        """

        通过CDB写回结果

        实际实现中应该广播到所有等待的保留站和寄存器

        """

        # 简化：假设每个周期可以完成一条指令

        if self.executing:

            # 取执行时间最长的（简化处理）

            rs_idx = self.executing.pop(0)

            rs = self.reservation_stations[rs_idx]



            # 计算结果

            vj = rs.vj if rs.vj is not None else 0.0

            vk = rs.vk if rs.vk is not None else 0.0



            if rs.op == OpType.ADD:

                result = vj + vk

            elif rs.op == OpType.SUB:

                result = vj - vk

            elif rs.op == OpType.MUL:

                result = vj * vk

            elif rs.op == OpType.DIV:

                result = vj / vk if vk != 0 else 0.0

            else:

                result = 0.0



            # 找到此保留站对应的ROB条目

            for i in range(self.num_rob):

                if self.rob[i].in_use and self.rob[i].instruction.dest == rs.dest:

                    self.rob[i].value = result

                    self.rob[i].ready = True

                    break



            # 释放保留站

            rs.busy = False

            rs.op = None

            rs.vj = None

            rs.vk = None

            rs.qj = None

            rs.qk = None



    def commit(self) -> Optional[Instruction]:

        """

        退役ROB头部的指令

        return: 退役的指令，如果没有则返回None

        """

        if not self.rob[self.rob_head].in_use:

            return None



        entry = self.rob[self.rob_head]

        if not entry.ready:

            return None



        # 写回寄存器

        self.registers.write(entry.instruction.dest, entry.value)



        # 释放ROB条目

        entry.in_use = False

        entry.ready = False



        # 移动头部指针

        retired_instr = entry.instruction

        self.rob_head = (self.rob_head + 1) % self.num_rob



        return retired_instr



    def step(self) -> List[str]:

        """

        执行一个时钟周期

        return: 此周期执行的操作描述

        """

        self.cycle += 1

        actions = []



        # 1. 尝试退役

        retired = self.commit()

        if retired:

            actions.append(f"Cycle {self.cycle}: 退役指令 I{retired.id} ({retired.op.value})")



        # 2. 写回结果

        if not self.executing:

            pass  # 简化处理



        # 3. 执行

        self._execute_ready_instructions()

        self._execute_instructions()



        # 4. 发射（简化：每周期发射一条）

        # 这在主循环中由外部控制



        return actions



    def clock(self):

        """执行一个时钟周期（简化版本）"""

        self.cycle += 1



        # 写回阶段

        self._write_result()



        # 执行阶段

        self._execute_ready_instructions()

        for i in range(self.num_rs):

            rs = self.reservation_stations[i]

            if rs.busy and rs.qj is None and rs.vj is not None and rs.qk is None and rs.vk is not None:

                if i not in self.executing:

                    self.executing.append(i)



        # 减少执行中指令的周期

        new_executing = []

        for i in self.executing:

            rs = self.reservation_stations[i]

            if hasattr(rs, 'remaining_cycles') and rs.remaining_cycles > 0:

                rs.remaining_cycles -= 1

                new_executing.append(i)

            elif not hasattr(rs, 'remaining_cycles'):

                new_executing.append(i)

        self.executing = new_executing



        # 退役

        self.commit()





def simulate_tomasulo():

    """

    模拟Tomasulo算法执行

    """

    print("=" * 60)

    print("Tomasulo算法模拟 - 流水线乱序执行")

    print("=" * 60)



    sim = TomasuloSimulator(num_reservation_stations=4, num_rob_entries=8)



    # 初始化寄存器值

    for i in range(1, 8):

        sim.registers.values[i] = float(i * 10)



    # 创建指令序列

    # 演示WAR/WAW hazard如何通过寄存器重命名解决

    instructions = [

        Instruction(1, OpType.MUL, 8, 1, 2),   # R8 = R1 * R2

        Instruction(2, OpType.ADD, 1, 3, 4),   # R1 = R3 + R4 (与I1存在WAW hazard)

        Instruction(3, OpType.SUB, 9, 8, 5),   # R9 = R8 - R5 (与I1存在RAW hazard)

        Instruction(4, OpType.ADD, 10, 9, 6),  # R10 = R9 + R6

        Instruction(5, OpType.MUL, 11, 10, 7), # R11 = R10 * R7

    ]



    print("\n初始寄存器状态:")

    for i in range(1, 12):

        print(f"  R{i} = {sim.registers.values[i]}")



    print("\n发射指令序列:")

    for instr in instructions:

        print(f"  I{instr.id}: R{instr.dest} = R{instr.src1} {instr.op.value} R{instr.src2}")



    print("\n执行过程:")

    print("-" * 60)



    issued_count = 0

    completed = []



    for cycle in range(1, 50):

        cycle_actions = []



        # 发射

        if issued_count < len(instructions):

            instr = instructions[issued_count]

            if sim.issue(instr):

                cycle_actions.append(f"发射 I{instr.id}")

                issued_count += 1



        # 写回（简化）

        sim._write_result()



        # 执行就绪检查

        sim._execute_ready_instructions()

        for i in range(sim.num_rs):

            rs = sim.reservation_stations[i]

            if rs.busy and rs.qj is None and rs.vj is not None and rs.qk is None and rs.vk is not None:

                if i not in sim.executing:

                    sim.executing.append(i)



        # 尝试退役

        retired = sim.commit()

        if retired:

            completed.append(retired)

            cycle_actions.append(f"退役 I{retired.id}")



        # 显示执行中的指令

        executing_str = ""

        if sim.executing:

            executing_str = f"执行中: RS{[i for i in sim.executing]}"



        print(f"Cycle {cycle:2d}: {', '.join(cycle_actions) if cycle_actions else '无操作'} {executing_str}")



        # 所有指令都退役则结束

        if len(completed) == len(instructions):

            break



    print("\n最终寄存器状态:")

    for i in range(1, 12):

        print(f"  R{i} = {sim.registers.values[i]}")



    print(f"\n总执行周期数: {sim.cycle}")

    print(f"退役指令数: {len(completed)}")

    print(f"指令级并行度(IPC): {len(instructions) / sim.cycle:.2f}")





if __name__ == "__main__":

    simulate_tomasulo()

