# -*- coding: utf-8 -*-
"""
算法实现：计算机体系结构 / reorder_buffer

本文件实现 reorder_buffer 相关的算法功能。
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import copy


class EntryState(Enum):
    """ROB条目状态"""
    PENDING = "PENDING"      # 等待执行
    EXECUTING = "EXECUTING"  # 正在执行
    COMPLETED = "COMPLETED"  # 已完成，待退役
    COMMITTED = "COMMITTED"  # 已退役
    CANCELED = "CANCELED"    # 已取消（由于异常）


class InstructionType(Enum):
    """指令类型"""
    ALU = "ALU"       # 算术逻辑指令
    LOAD = "LOAD"     # 加载指令
    STORE = "STORE"   # 存储指令
    BRANCH = "BRANCH" # 分支指令


@dataclass
class ROBEntry:
    """
    重排序缓冲区条目

    属性：
    - id: 条目序号（位置）
    - instruction: 原始指令信息
    - state: 当前状态
    - destination: 目标寄存器或内存地址
    - value: 执行结果值
    - exception: 是否有异常
    - exception_type: 异常类型
    """
    id: int
    instruction: Dict[str, Any] = field(default_factory=dict)
    state: EntryState = EntryState.PENDING
    destination: Any = None  # 寄存器号或内存地址
    value: Any = None
    exception: bool = False
    exception_type: Optional[str] = None

    def __repr__(self):
        instr = self.instruction
        instr_str = f"Op={instr.get('op', '?')}"
        if 'dest' in instr:
            instr_str += f", Dest=Reg{self.destination}"
        return f"ROB[{self.id}]({instr_str}, state={self.state.value})"


class RegisterStatus:
    """
    寄存器状态表
    跟踪每个寄存器的值是否pending于某个ROB条目
    """

    def __init__(self, num_registers=32):
        self.num_registers = num_registers
        # 寄存器值
        self.values = [0.0] * num_registers
        # 每个寄存器对应的ROB条目ID，None表示值就绪
        self.rob_tag = [None] * num_registers
        # 寄存器名称（可选）
        self.names = [f"R{i}" for i in range(num_registers)]

    def is_ready(self, reg: int) -> bool:
        """检查寄存器值是否就绪"""
        return self.rob_tag[reg] is None

    def read(self, reg: int) -> float:
        """读取寄存器值（假设值已就绪）"""
        return self.values[reg]

    def write(self, reg: int, value: float):
        """写入寄存器"""
        self.values[reg] = value
        self.rob_tag[reg] = None

    def set_pending(self, reg: int, rob_id: int):
        """设置寄存器等待某个ROB条目完成"""
        self.rob_tag[reg] = rob_id

    def get_pending_rob(self, reg: int) -> Optional[int]:
        """获取寄存器pending的ROB ID"""
        return self.rob_tag[reg]


class ReorderBuffer:
    """
    重排序缓冲区 (ROB)

    实现顺序发射、顺序退役的缓冲区。
    指令发射时分配ROB条目，执行完成后填写结果，
    退役时按顺序将结果写回寄存器和内存。

    参数：
    - capacity: ROB容量
    """

    def __init__(self, capacity=16):
        self.capacity = capacity
        # ROB条目数组
        self.entries: List[Optional[ROBEntry]] = [None] * capacity
        # 头部指针（最早发射的指令）
        self.head = 0
        # 尾部指针（下一个可用位置）
        self.tail = 0
        # 已使用的条目数
        self.count = 0

        # 统计信息
        self.total_instructions = 0
        self.total_committed = 0

    def is_empty(self) -> bool:
        """ROB是否为空"""
        return self.count == 0

    def is_full(self) -> bool:
        """ROB是否已满"""
        return self.count >= self.capacity

    def _advance(self, pointer: int) -> int:
        """环形缓冲区的指针前进"""
        return (pointer + 1) % self.capacity

    def space_available(self) -> int:
        """可用空间"""
        return self.capacity - self.count

    def allocate(self, instruction: Dict[str, Any], destination: Any) -> Optional[int]:
        """
        分配一个新的ROB条目
        param instruction: 指令信息
        param destination: 目标寄存器或内存地址
        return: 分配的ROB条目ID，失败返回None
        """
        if self.is_full():
            return None

        # 创建新条目
        entry = ROBEntry(
            id=self.tail,
            instruction=copy.deepcopy(instruction),
            destination=destination,
            state=EntryState.PENDING
        )

        self.entries[self.tail] = entry
        self.tail = self._advance(self.tail)
        self.count += 1
        self.total_instructions += 1

        return entry.id

    def get_entry(self, entry_id: int) -> Optional[ROBEntry]:
        """获取指定ID的ROB条目"""
        if 0 <= entry_id < self.capacity:
            return self.entries[entry_id]
        return None

    def mark_completed(self, entry_id: int, value: Any, exception: bool = False, exception_type: str = None):
        """
        标记ROB条目为已完成
        param entry_id: 条目ID
        param value: 执行结果值
        param exception: 是否有异常
        """
        entry = self.get_entry(entry_id)
        if entry:
            entry.value = value
            entry.state = EntryState.COMPLETED
            entry.exception = exception
            entry.exception_type = exception_type

    def can_commit(self) -> bool:
        """检查是否可以退役（头部条目已完成）"""
        if self.is_empty():
            return False
        entry = self.entries[self.head]
        return entry is not None and entry.state == EntryState.COMPLETED

    def commit(self, registers: RegisterStatus, memory: Dict[int, float] = None) -> Optional[Dict[str, Any]]:
        """
        退役头部的ROB条目
        param registers: 寄存器状态表
        param memory: 内存（用于STORE指令）
        return: 退役的指令信息，如果有异常则返回异常信息
        """
        if not self.can_commit():
            return None

        entry = self.entries[self.head]

        # 检查是否有异常
        if entry.exception:
            result = {
                'type': 'exception',
                'entry_id': entry.id,
                'exception_type': entry.exception_type,
                'instruction': entry.instruction
            }
            # 取消此条之后的所有条目（简化处理）
            self._cancel_all()
            return result

        # 写回结果
        instr = entry.instruction
        op_type = instr.get('type', 'ALU')

        if op_type == 'STORE' and memory is not None:
            # STORE指令写入内存
            addr = entry.destination
            memory[addr] = entry.value
        elif entry.destination is not None and isinstance(entry.destination, int):
            # ALU/LOAD指令写回寄存器
            registers.write(entry.destination, entry.value)

        # 更新条目状态
        entry.state = EntryState.COMMITTED
        self.entries[self.head] = None
        self.head = self._advance(self.head)
        self.count -= 1
        self.total_committed += 1

        return {
            'type': 'committed',
            'entry_id': entry.id,
            'instruction': entry.instruction,
            'value': entry.value
        }

    def _cancel_all(self):
        """取消所有条目（发生异常时调用）"""
        while not self.is_empty():
            entry = self.entries[self.head]
            if entry:
                entry.state = EntryState.CANCELED
                self.entries[self.head] = None
            self.head = self._advance(self.head)
        self.count = 0

    def get_status(self) -> Dict[str, Any]:
        """获取ROB状态"""
        return {
            'capacity': self.capacity,
            'count': self.count,
            'head': self.head,
            'tail': self.tail,
            'space_available': self.space_available(),
            'is_full': self.is_full(),
            'total_instructions': self.total_instructions,
            'total_committed': self.total_committed
        }

    def __repr__(self) -> str:
        lines = [f"ROB Status: {self.count}/{self.capacity} entries"]
        lines.append(f"Head={self.head}, Tail={self.tail}")
        for i in range(self.capacity):
            entry = self.entries[i]
            if entry:
                lines.append(f"  [{i}] {entry}")
        return "\n".join(lines)


def simulate_rob():
    """
    模拟ROB工作过程
    """
    print("=" * 60)
    print("Reorder Buffer (ROB) 模拟")
    print("=" * 60)

    # 初始化
    rob = ReorderBuffer(capacity=8)
    registers = RegisterStatus(num_registers=8)
    memory = {}

    # 初始化寄存器值
    for i in range(1, 8):
        registers.values[i] = float(i * 10)

    print("\n初始寄存器状态:")
    for i in range(1, 8):
        print(f"  {registers.names[i]} = {registers.values[i]}")

    # 模拟指令发射
    # 指令格式：{id, type, op, dest, src1, src2}
    instructions = [
        {'id': 1, 'type': 'ALU', 'op': 'ADD', 'dest': 8, 'src1': 1, 'src2': 2},
        {'id': 2, 'type': 'ALU', 'op': 'MUL', 'dest': 9, 'src1': 3, 'src2': 4},
        {'id': 3, 'type': 'ALU', 'op': 'SUB', 'dest': 10, 'src1': 5, 'src2': 6},
        {'id': 4, 'type': 'LOAD', 'op': 'LOAD', 'dest': 11, 'addr': 0x1000},
        {'id': 5, 'type': 'STORE', 'op': 'STORE', 'addr': 0x1000, 'value': 999},
    ]

    print("\n发射指令:")
    for instr in instructions:
        dest_str = f"Reg{instr.get('dest', '?')}" if instr.get('dest') else f"Mem0x{instr.get('addr', 0):X}"
        print(f"  I{instr['id']}: {instr['op']} -> {dest_str}")

    print("\n" + "-" * 60)
    print("执行过程:")
    print("-" * 60)

    issued = []
    completed_ids = set()
    cycle = 0

    while len(completed_ids) < len(instructions) or not rob.is_empty():
        cycle += 1
        actions = []

        # 发射指令
        if len(issued) < len(instructions):
            instr = instructions[len(issued)]
            dest = instr.get('dest', instr.get('addr'))
            rob_id = rob.allocate(instr, dest)
            if rob_id is not None:
                issued.append(instr)
                # 设置寄存器pending
                if 'dest' in instr:
                    registers.set_pending(instr['dest'], rob_id)
                actions.append(f"发射 I{instr['id']}->ROB[{rob_id}]")

        # 模拟执行完成（简化：按顺序完成）
        for i, instr in enumerate(issued):
            instr_id = instr['id']
            if instr_id in completed_ids:
                continue

            # 找到对应的ROB条目
            for eid in range(rob.capacity):
                entry = rob.get_entry(eid)
                if entry and entry.instruction.get('id') == instr_id:
                    if entry.state == EntryState.PENDING:
                        # 模拟执行完成
                        # 计算结果
                        if instr['type'] == 'ALU':
                            v1 = registers.read(instr['src1'])
                            v2 = registers.read(instr['src2'])
                            if instr['op'] == 'ADD':
                                val = v1 + v2
                            elif instr['op'] == 'SUB':
                                val = v1 - v2
                            elif instr['op'] == 'MUL':
                                val = v1 * v2
                            else:
                                val = 0
                        elif instr['type'] == 'LOAD':
                            val = memory.get(instr['addr'], 0)
                        elif instr['type'] == 'STORE':
                            val = instr['value']
                            entry.destination = instr['addr']
                        else:
                            val = 0

                        rob.mark_completed(eid, val)
                        completed_ids.add(instr_id)
                        actions.append(f"完成 I{instr_id}")
                    break

        # 尝试退役
        if rob.can_commit():
            result = rob.commit(registers, memory)
            if result:
                if result['type'] == 'exception':
                    actions.append(f"异常: {result['exception_type']}")
                else:
                    actions.append(f"退役 I{result['entry_id']}")

        print(f"Cycle {cycle:2d}: {', '.join(actions) if actions else '无操作'}")

        if cycle > 100:
            break

    print("\n" + "=" * 60)
    print("最终状态:")
    print("=" * 60)

    print("\n寄存器状态:")
    for i in range(1, 12):
        if registers.values[i] != 0:
            print(f"  R{i} = {registers.values[i]}")

    print(f"\n内存内容:")
    for addr, val in sorted(memory.items()):
        print(f"  0x{addr:X}: {val}")

    print(f"\nROB统计: 总发射={rob.total_instructions}, 总退役={rob.total_committed}")


if __name__ == "__main__":
    simulate_rob()
