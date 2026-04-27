# -*- coding: utf-8 -*-
"""
算法实现：计算机体系结构 / instruction_scheduling

本文件实现 instruction_scheduling 相关的算法功能。
"""

from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import heapq


class OpType(Enum):
    """指令类型"""
    ADD = "ADD"
    SUB = "SUB"
    MUL = "MUL"
    DIV = "DIV"
    LOAD = "LOAD"
    STORE = "STORE"


@dataclass
class Instruction:
    """指令"""
    id: int
    op: OpType
    dest: int              # 目的寄存器
    src1: int              # 源寄存器1
    src2: int              # 源寄存器2
    latency: int = 1       # 执行延迟
    issued: bool = False   # 是否已发射
    executed: bool = False
    completed: bool = False


@dataclass
class PipelineStage:
    """流水线阶段"""
    name: str
    busy: bool = False
    instruction: Optional[Instruction] = None


class FunctionalUnit:
    """功能单元"""

    def __init__(self, name: str, latency: int = 1):
        self.name = name
        self.latency = latency
        self.busy = False
        self.current_instruction: Optional[Instruction] = None
        self.remaining_cycles = 0

    def can_issue(self) -> bool:
        """是否可以发射新指令"""
        return not self.busy

    def issue(self, instr: Instruction):
        """发射指令"""
        self.busy = True
        self.current_instruction = instr
        self.remaining_cycles = self.latency

    def step(self) -> bool:
        """执行一个周期，返回是否完成"""
        if not self.busy:
            return False

        self.remaining_cycles -= 1
        if self.remaining_cycles <= 0:
            self.busy = False
            completed = self.current_instruction
            self.current_instruction = None
            return True
        return False


class RegisterFile:
    """寄存器文件"""

    def __init__(self, num_regs: int = 16):
        self.num_regs = num_regs
        self.values = [0.0] * num_regs
        self.busy = [False] * num_regs  # 寄存器是否pending
        self.allocated_to: Dict[int, int] = {}  # 指令ID -> 寄存器

    def is_available(self, reg: int) -> bool:
        """寄存器是否可用"""
        return not self.busy[reg] and reg not in self.allocated_to

    def allocate(self, instr_id: int, reg: int):
        """分配寄存器给指令"""
        self.allocated_to[reg] = instr_id

    def free(self, reg: int):
        """释放寄存器"""
        if reg in self.allocated_to:
            del self.allocated_to[reg]

    def write(self, reg: int, value: float):
        """写寄存器"""
        self.values[reg] = value
        self.busy[reg] = False


class ListScheduler:
    """
    List Scheduling 调度器

    算法：
    1. 构建DAG（依赖图）
    2. 计算每条指令的优先级（通过分析关键路径）
    3. 每次调度时，从就绪指令中选择优先级最高的
    4. 选择一个可用的功能单元发射

    支持：
    - 乱序发射
    - 资源约束（功能单元数量）
    - 依赖约束（RAW hazard）
    """

    def __init__(self, num_issue_width: int = 2, num_regs: int = 16):
        self.num_issue_width = num_issue_width
        self.num_regs = num_regs

        # 功能单元配置
        self.functional_units = [
            FunctionalUnit("ALU1", latency=1),
            FunctionalUnit("ALU2", latency=1),
            FunctionalUnit("MUL", latency=3),
            FunctionalUnit("LOAD", latency=2),
            FunctionalUnit("STORE", latency=1),
        ]

        # 寄存器文件
        self.registers = RegisterFile(num_regs)

        # 调度状态
        self.instructions: List[Instruction] = []
        self.ready_queue: List[int] = []  # 就绪指令ID列表
        self.executing: List[int] = []  # 正在执行的指令ID

        # 依赖图：{instr_id: set of dependent instr_ids}
        self.dependencies: Dict[int, Set[int]] = {}
        self.dependents: Dict[int, Set[int]] = {}  # 反向依赖

        # 统计
        self.cycle = 0
        self.schedule_length = 0

    def add_instruction(self, instr: Instruction):
        """添加指令"""
        self.instructions.append(instr)

    def _build_dependency_graph(self):
        """构建依赖图"""
        self.dependencies = {i: set() for i in range(len(self.instructions))}
        self.dependents = {i: set() for i in range(len(self.instructions))}

        for i, instr in enumerate(self.instructions):
            for j, other in enumerate(self.instructions):
                if i == j:
                    continue
                # 检查RAW hazard：other的结果是instr的源操作数
                if other.dest == instr.src1 or other.dest == instr.src2:
                    # i依赖于j
                    self.dependencies[i].add(j)
                    self.dependents[j].add(i)

    def _compute_priorities(self) -> Dict[int, int]:
        """
        计算指令优先级（关键路径长度）
        使用逆拓扑顺序计算
        """
        # 计算每条指令的"高度"（到叶子的最长路径）
        height: Dict[int, int] = {}

        def compute_height(instr_id: int) -> int:
            if instr_id in height:
                return height[instr_id]

            max_dep_height = 0
            for dep_id in self.dependencies[instr_id]:
                max_dep_height = max(max_dep_height, compute_height(dep_id))

            height[instr_id] = max_dep_height + self.instructions[instr_id].latency
            return height[instr_id]

        for i in range(len(self.instructions)):
            compute_height(i)

        return height

    def _update_ready_queue(self):
        """更新就绪队列"""
        for i, instr in enumerate(self.instructions):
            if instr.issued:
                continue

            # 检查所有依赖是否已完成
            deps_done = all(
                self.instructions[d].completed
                for d in self.dependencies[i]
            )

            if deps_done:
                if i not in self.ready_queue:
                    self.ready_queue.append(i)

    def _select_instruction(self, priorities: Dict[int, int]) -> Optional[int]:
        """
        选择指令
        使用优先级选择：优先选择关键路径上的指令
        """
        if not self.ready_queue:
            return None

        # 按优先级排序（优先级高的在前）
        self.ready_queue.sort(key=lambda x: -priorities[x])
        return self.ready_queue[0]

    def _find_available_unit(self, instr: Instruction) -> Optional[FunctionalUnit]:
        """找可用的功能单元"""
        required_type = instr.op

        for unit in self.functional_units:
            if unit.name.startswith(required_type.value) and unit.can_issue():
                return unit
            # 通用ALU
            if required_type in (OpType.ADD, OpType.SUB) and unit.name.startswith("ALU"):
                if unit.can_issue():
                    return unit

        return None

    def schedule(self) -> int:
        """
        执行调度
        return: 调度长度（总周期数）
        """
        self._build_dependency_graph()
        priorities = self._compute_priorities()

        print("\n调度前的DAG（依赖图）:")
        for i, instr in enumerate(self.instructions):
            deps = self.dependencies[i]
            if deps:
                dep_ids = ", ".join(str(d) for d in deps)
                print(f"  I{instr.id} 依赖: [{dep_ids}], 优先级={priorities[i]}")
            else:
                print(f"  I{instr.id} 无依赖, 优先级={priorities[i]}")

        print(f"\n就绪队列初始: {self.ready_queue}")

        self.ready_queue = []
        self._update_ready_queue()

        print(f"\n就绪队列更新后: {self.ready_queue}")

        # 调度循环
        while any(not instr.completed for instr in self.instructions):
            self.cycle += 1
            cycle_actions = []

            # 1. 发射阶段（最多num_issue_width条）
            issued_this_cycle = 0
            while issued_this_cycle < self.num_issue_width:
                instr_id = self._select_instruction(priorities)
                if instr_id is None:
                    break

                instr = self.instructions[instr_id]
                unit = self._find_available_unit(instr)

                if unit is None:
                    break  # 没有可用单元

                # 发射
                unit.issue(instr)
                instr.issued = True
                self.ready_queue.remove(instr_id)
                self.executing.append(instr_id)
                cycle_actions.append(f"发射 I{instr.id} -> {unit.name}")
                issued_this_cycle += 1

            # 2. 执行阶段
            completed_this_cycle = []
            for unit in self.functional_units:
                if unit.step():  # 指令完成
                    if unit.current_instruction:
                        completed_id = unit.current_instruction.id - 1
                        completed_this_cycle.append(completed_id)

            for instr_id in completed_this_cycle:
                self.instructions[instr_id].completed = True
                self.instructions[instr_id].executed = True
                if instr_id in self.executing:
                    self.executing.remove(instr_id)
                cycle_actions.append(f"完成 I{self.instructions[instr_id].id}")

            # 3. 更新就绪队列
            self._update_ready_queue()

            # 打印周期信息
            if cycle_actions:
                print(f"Cycle {self.cycle:2d}: {', '.join(cycle_actions)}")

        self.schedule_length = self.cycle
        return self.cycle

    def get_statistics(self) -> Dict[str, any]:
        """获取调度统计"""
        return {
            'total_instructions': len(self.instructions),
            'schedule_length': self.schedule_length,
            'ilp': len(self.instructions) / self.schedule_length if self.schedule_length > 0 else 0,
            'utilization': sum(
                1 for i in self.instructions if i.issued
            ) / self.schedule_length / self.num_issue_width if self.schedule_length > 0 else 0
        }


class RegisterAllocator:
    """
    简单的寄存器分配器

    使用图着色算法（简化版）的思想：
    1. 构建寄存器冲突图
    2. 尝试分配颜色（寄存器）
    3. 如果分配失败，使用溢出（spill）策略
    """

    def __init__(self, num_physical_regs: int = 8):
        self.num_physical_regs = num_physical_regs
        # 虚拟寄存器 -> 物理寄存器映射
        self.allocations: Dict[int, int] = {}
        # 物理寄存器 -> 虚拟寄存器映射
        self.reverse_map: Dict[int, int] = {}
        # 溢出列表
        self.spilled: Set[int] = set()

    def allocate(self, virtual_reg: int, conflicting_regs: Set[int]) -> Optional[int]:
        """
        为虚拟寄存器分配物理寄存器
        param virtual_reg: 虚拟寄存器号
        param conflicting_regs: 与此寄存器冲突的虚拟寄存器集合
        return: 分配的物理寄存器号，或None表示需要溢出
        """
        # 找到所有冲突虚拟寄存器对应的物理寄存器
        used_physical = set()
        for cr in conflicting_regs:
            if cr in self.allocations:
                used_physical.add(self.allocations[cr])

        # 找一个空闲物理寄存器
        for phys in range(self.num_physical_regs):
            if phys not in used_physical and phys not in self.reverse_map:
                self.allocations[virtual_reg] = phys
                self.reverse_map[phys] = virtual_reg
                return phys

        # 需要溢出
        return None

    def free(self, virtual_reg: int):
        """释放虚拟寄存器"""
        if virtual_reg in self.allocations:
            phys = self.allocations[virtual_reg]
            del self.allocations[virtual_reg]
            del self.reverse_map[phys]


def simulate_list_scheduling():
    """
    模拟List Scheduling
    """
    print("=" * 60)
    print("List Scheduling 模拟")
    print("=" * 60)

    # 创建调度器：2发射宽度
    scheduler = ListScheduler(num_issue_width=2, num_regs=16)

    # 创建指令序列
    # 演示如何调度以避免hazard并最大化ILP
    instructions = [
        Instruction(1, OpType.MUL, dest=1, src1=1, src2=2, latency=3),   # R1 = R1 * R2
        Instruction(2, OpType.ADD, dest=3, src1=1, src2=4, latency=1),   # R3 = R1 + R4 (依赖I1)
        Instruction(3, OpType.SUB, dest=5, src1=3, src2=6, latency=1),   # R5 = R3 - R6 (依赖I2)
        Instruction(4, OpType.ADD, dest=7, src1=2, src2=8, latency=1),   # R7 = R2 + R8 (独立)
        Instruction(5, OpType.MUL, dest=9, src1=7, src2=5, latency=3),   # R9 = R7 * R5 (依赖I3,I4)
        Instruction(6, OpType.ADD, dest=11, src1=9, src2=10, latency=1), # R11 = R9 + R10 (依赖I5)
    ]

    for instr in instructions:
        scheduler.add_instruction(instr)

    print("\n指令序列:")
    for instr in instructions:
        print(f"  I{instr.id}: R{instr.dest} = R{instr.src1} {instr.op.value} R{instr.src2} (latency={instr.latency})")

    # 初始化就绪队列
    scheduler.ready_queue = [0]  # I1没有依赖

    print("\n" + "-" * 60)
    print("调度过程:")
    print("-" * 60)

    schedule_length = scheduler.schedule()

    stats = scheduler.get_statistics()
    print(f"\n调度结果:")
    print(f"  总周期数: {stats['schedule_length']}")
    print(f"  指令数: {stats['total_instructions']}")
    print(f"  ILP (Instructions Per Cycle): {stats['ilp']:.2f}")


if __name__ == "__main__":
    simulate_list_scheduling()
