# -*- coding: utf-8 -*-
"""
算法实现：计算机体系结构_2 / reservation_station

本文件实现 reservation_station 相关的算法功能。
"""

import random
from typing import List, Optional, Dict, Set
from dataclasses import dataclass, field
from enum import Enum, auto


class RS_State(Enum):
    """预约站条目状态"""
    FREE = auto()           # 空闲
    WAITING = auto()        # 等待操作数
    READY = auto()          # 操作数就绪，等待发射
    ISSUED = auto()         # 已发射到功能单元


@dataclass
class RS_Entry:
    """预约站条目"""
    id: int = 0                     # 条目ID
    opcode: str = ""                # 操作码
    dest: Optional[int] = None      # 目的物理寄存器
    src1_phys: Optional[int] = None # 源操作数1物理寄存器
    src2_phys: Optional[int] = None # 源操作数2物理寄存器
    src1_ready: bool = False       # 源1是否就绪
    src2_ready: bool = False       # 源2是否就绪
    src1_value: Optional[int] = None  # 源1值（就绪后保存）
    src2_value: Optional[int] = None  # 源2值（就绪后保存）
    state: RS_State = RS_State.FREE
    age: int = 0                   # 年龄（发射顺序）


class Physical_Register_File:
    """物理寄存器文件"""
    def __init__(self, num_regs: int = 64):
        self.num_regs = num_regs
        self.values: List[Optional[int]] = [None] * num_regs
        self.valid: List[bool] = [False] * num_regs  # 是否已写入


    def write(self, reg: int, value: int):
        """写入物理寄存器"""
        if 0 <= reg < self.num_regs:
            self.values[reg] = value
            self.valid[reg] = True


    def read(self, reg: int) -> Optional[int]:
        """读取物理寄存器值"""
        if 0 <= reg < self.num_regs and self.valid[reg]:
            return self.values[reg]
        return None


class Functional_Unit:
    """功能单元"""
    def __init__(self, name: str, latency: int = 1):
        self.name = name
        self.latency = latency              # 执行延迟（周期数）
        self.busy: bool = False             # 是否忙
        self.current_op: Optional[RS_Entry] = None
        self.cycles_remaining: int = 0     # 剩余执行周期


    def start_execution(self, op: RS_Entry):
        """开始执行一条操作"""
        self.busy = True
        self.current_op = op
        self.cycles_remaining = self.latency


    def step(self) -> Optional[RS_Entry]:
        """功能单元执行一步"""
        if not self.busy:
            return None
        self.cycles_remaining -= 1
        if self.cycles_remaining <= 0:
            op = self.current_op
            self.busy = False
            self.current_op = None
            return op
        return None


class Reservation_Station:
    """预约站（Tomasulo算法核心）"""
    def __init__(self, name: str, size: int = 8, fu: Functional_Unit = None):
        self.name = name
        self.size = size
        self.entries: List[Optional[RS_Entry]] = [None] * size
        self.count: int = 0
        self.next_id: int = 0
        self.fu = fu if fu else Functional_Unit(name, latency=1)


    def is_full(self) -> bool:
        """预约站是否已满"""
        return self.count >= self.size


    def is_empty(self) -> bool:
        """预约站是否为空"""
        return self.count == 0


    def insert(self, opcode: str, dest: Optional[int], src1: Optional[int], src2: Optional[int]) -> Optional[int]:
        """插入一条指令到预约站"""
        if self.is_full():
            return None
        # 找到空闲条目
        for i in range(self.size):
            if self.entries[i] is None:
                entry = RS_Entry(
                    id=self.next_id,
                    opcode=opcode,
                    dest=dest,
                    src1_phys=src1,
                    src2_phys=src2,
                    src1_ready=(src1 is None),
                    src2_ready=(src2 is None),
                    state=RS_State.WAITING,
                    age=self.count
                )
                self.next_id += 1
                self.entries[i] = entry
                self.count += 1
                return entry.id
        return None


    def check_operands_ready(self, entry: RS_Entry, phys_reg_file: Physical_Register_File) -> bool:
        """检查操作数是否就绪"""
        if entry.src1_phys is not None and not entry.src1_ready:
            val = phys_reg_file.read(entry.src1_phys)
            if val is not None:
                entry.src1_value = val
                entry.src1_ready = True
        if entry.src2_phys is not None and not entry.src2_ready:
            val = phys_reg_file.read(entry.src2_phys)
            if val is not None:
                entry.src2_value = val
                entry.src2_ready = True
        return entry.src1_ready and entry.src2_ready


    def select_issue(self, phys_reg_file: Physical_Register_File) -> Optional[RS_Entry]:
        """选择一条就绪指令发射到功能单元"""
        # 按年龄（程序顺序）选择最老的就绪指令
        oldest_ready: Optional[RS_Entry] = None
        oldest_idx = -1
        for i in range(self.size):
            entry = self.entries[i]
            if entry is not None and entry.state == RS_State.WAITING:
                if self.check_operands_ready(entry, phys_reg_file):
                    if oldest_ready is None or entry.age < oldest_ready.age:
                        oldest_ready = entry
                        oldest_idx = i
        if oldest_ready is not None:
            oldest_ready.state = RS_State.ISSUED
            self.fu.start_execution(oldest_ready)
            return oldest_ready
        return None


    def remove_completed(self, entry_id: int):
        """移除已完成的条目"""
        for i in range(self.size):
            entry = self.entries[i]
            if entry is not None and entry.id == entry_id:
                self.entries[i] = None
                self.count -= 1
                break


class Tomasulo_Simulator:
    """Tomasulo算法模拟器"""
    def __init__(self):
        # 创建预约站（2个ALU RS）
        self.rs_alu1 = Reservation_Station("ALU1", size=8, fu=Functional_Unit("ALU1", latency=2))
        self.rs_alu2 = Reservation_Station("ALU2", size=8, fu=Functional_Unit("ALU2", latency=2))
        # 创建LSU预约站
        self.rs_lsu = Reservation_Station("LSU", size=8, fu=Functional_Unit("LSU", latency=3))
        # 物理寄存器文件
        self.phys_reg = Physical_Register_File(num_regs=64)
        # CDB（公共数据总线）
        self.cdb: Dict[int, int] = {}  # reg -> value
        # 统计
        self.cycles: int = 0
        self.instructions_issued: int = 0
        self.instructions_completed: int = 0


    def issue(self, opcode: str, dest: Optional[int], src1: Optional[int], src2: Optional[int]) -> bool:
        """发射指令到合适的预约站"""
        rs = self._select_rs(opcode)
        if rs is None or rs.is_full():
            return False
        entry_id = rs.insert(opcode, dest, src1, src2)
        if entry_id is not None:
            self.instructions_issued += 1
            return True
        return False


    def _select_rs(self, opcode: str) -> Optional[Reservation_Station]:
        """选择合适的预约站"""
        if opcode in ["ADD", "SUB", "MUL", "DIV"]:
            return self.rs_alu1 if self.rs_alu1.count <= self.rs_alu2.count else self.rs_alu2
        elif opcode in ["LOAD", "STORE"]:
            return self.rs_lsu
        return self.rs_alu1


    def execute_cycle(self):
        """执行一个周期"""
        self.cycles += 1
        # 尝试发射就绪指令
        for rs in [self.rs_alu1, self.rs_alu2, self.rs_lsu]:
            while not rs.is_empty():
                op = rs.select_issue(self.phys_reg)
                if op is None:
                    break
        # 功能单元执行
        for rs in [self.rs_alu1, self.rs_alu2, self.rs_lsu]:
            completed = rs.fu.step()
            if completed is not None:
                # 通过CDB广播结果
                if completed.dest is not None:
                    self.cdb[completed.dest] = completed.result_value if completed.result_value else 0
                    self.phys_reg.write(completed.dest, self.cdb[completed.dest])
                rs.remove_completed(completed.id)
                self.instructions_completed += 1
        # 更新所有RS中等待该结果的条目
        self._broadcast_cdb()


    def _broadcast_cdb(self):
        """通过CDB广播结果到所有等待的预约站"""
        if not self.cdb:
            return
        for reg, value in self.cdb.items():
            for rs in [self.rs_alu1, self.rs_alu2, self.rs_lsu]:
                for entry in rs.entries:
                    if entry is not None:
                        if entry.src1_phys == reg and not entry.src1_ready:
                            entry.src1_value = value
                            entry.src1_ready = True
                        if entry.src2_phys == reg and not entry.src2_ready:
                            entry.src2_value = value
                            entry.src2_ready = True
        self.cdb.clear()


def basic_test():
    """基本功能测试"""
    print("=== Reservation Station 模拟器测试 ===")
    sim = Tomasulo_Simulator()
    # 发射一些指令
    print("\n发射指令:")
    instructions = [
        ("ADD", 16, 1, 2),      # r16 = r1 + r2
        ("ADD", 17, 2, 3),      # r17 = r2 + r3
        ("MUL", 18, 16, 17),    # r18 = r16 * r17 (依赖前两条)
        ("ADD", 19, 18, 4),      # r19 = r18 + r4 (依赖第三条)
        ("LOAD", 20, 5, None),   # r20 = mem[r5]
    ]
    for i, (opcode, dest, src1, src2) in enumerate(instructions):
        success = sim.issue(opcode, dest, src1, src2)
        print(f"  {i}: {opcode} r{dest} = r{src1} {',' if src2 else ''} {f'r{src2}' if src2 else ''} -> {'成功' if success else '失败'}")
    # 模拟执行
    print("\n执行周期:")
    for cycle in range(10):
        sim.execute_cycle()
        total_busy = sim.rs_alu1.count + sim.rs_alu2.count + sim.rs_lsu.count
        print(f"  Cycle {sim.cycles}: 已完成={sim.instructions_completed}, RS占用={total_busy}")
        if sim.instructions_completed >= len(instructions):
            break
    print(f"\n最终统计:")
    print(f"  总周期: {sim.cycles}")
    print(f"  发射指令数: {sim.instructions_issued}")
    print(f"  完成指令数: {sim.instructions_completed}")


if __name__ == "__main__":
    basic_test()
