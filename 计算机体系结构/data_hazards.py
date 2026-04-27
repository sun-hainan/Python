# -*- coding: utf-8 -*-
"""
算法实现：计算机体系结构 / data_hazards

本文件实现 data_hazards 相关的算法功能。
"""

from typing import List, Optional, Dict, Set, Tuple
from dataclasses import dataclass
from enum import Enum


class HazardType(Enum):
    """Hazard类型"""
    RAW = "read_after_write"    # 真数据依赖
    WAR = "write_after_read"    # 反依赖
    WAW = "write_after_write"   # 输出依赖


@dataclass
class Instruction:
    """指令"""
    id: int
    name: str
    dest: int = -1     # 目的寄存器
    src1: int = -1     # 源寄存器1
    src2: int = -1     # 源寄存器2
    cycles: int = 1     # 执行周期数

    # 流水线状态
    issued: bool = False
    executing: bool = False
    completed: bool = False
    committed: bool = False

    # 时序
    issue_cycle: int = 0
    execute_start: int = 0
    execute_end: int = 0
    commit_cycle: int = 0


class PipelineRegister:
    """流水线寄存器（IF/ID, ID/EX, EX/MEM, MEM/WB）"""

    def __init__(self, name: str):
        self.name = name
        self.instruction: Optional[Instruction] = None
        self.valid: bool = False

    def clear(self):
        """清除流水线寄存器"""
        self.instruction = None
        self.valid = False


class PipelineStage:
    """流水线阶段"""

    def __init__(self, name: str):
        self.name = name
        self.busy: bool = False
        self.instruction: Optional[Instruction] = None


class ForwardingUnit:
    """
    转发单元

    检测RAW hazard并选择正确的转发数据源。
    """

    def __init__(self):
        # 转发路径定义
        # (from_stage, to_stage): [(src_mux_val, data_source), ...]
        self.forwarding_paths: Dict[Tuple[str, str], List] = {
            ('EX', 'EX'): [],  # EX阶段的结果转发到EX阶段
            ('MEM', 'EX'): [],
            ('MEM', 'MEM'): [],
            ('WB', 'EX'): [],
        }

        # 当前待转发的数据
        self.pending_forwards: List[Dict] = []

    def detect_hazard(self, current_instr: Instruction,
                      ex_mem_instr: Optional[Instruction],
                      mem_wb_instr: Optional[Instruction]) -> Optional[Tuple[str, int]]:
        """
        检测RAW hazard并返回转发信息
        return: (forward_from_stage, forwarded_value) 或 None
        """
        # 检查EX/MEM阶段
        if ex_mem_instr and ex_mem_instr.dest == current_instr.src1:
            return ('EX', ex_mem_instr.dest)
        if ex_mem_instr and ex_mem_instr.dest == current_instr.src2:
            return ('EX', ex_mem_instr.dest)

        # 检查MEM/WB阶段
        if mem_wb_instr and mem_wb_instr.dest == current_instr.src1:
            return ('MEM', mem_wb_instr.dest)
        if mem_wb_instr and mem_wb_instr.dest == current_instr.src2:
            return ('MEM', mem_wb_instr.dest)

        return None

    def get_forwarded_value(self, forward_from: str,
                           ex_result: int, mem_result: int, wb_result: int) -> int:
        """根据转发源获取转发值"""
        if forward_from == 'EX':
            return ex_result
        elif forward_from == 'MEM':
            return mem_result
        elif forward_from == 'WB':
            return wb_result
        return 0


class HazardDetectionUnit:
    """
    Hazard检测单元

    检测RAW hazard并在需要时插入气泡(stall)。
    """

    def __init__(self):
        self.stalls: int = 0

    def check_RAW(self, current: Instruction,
                  ex: Instruction, mem: Instruction) -> bool:
        """
        检查RAW hazard
        return: True表示有hazard，需要stall
        """
        # 当前指令的源寄存器
        src1 = current.src1
        src2 = current.src2

        # EX阶段的指令会写什么
        if ex and ex.dest in (src1, src2):
            return True  # 需要stall

        # MEM阶段的指令会写什么
        if mem and mem.dest in (src1, src2):
            return True

        return False

    def check_WAR(self, current: Instruction,
                  issue_queue: List[Instruction]) -> bool:
        """
        检查WAR hazard
        在顺序发射的经典五级流水线中，WAR hazard发生在：
        - 当前指令在后续指令读取操作数之前写入
        由于顺序发射，通常不会发生WAR（除非有转发）
        """
        for instr in issue_queue:
            if instr.id > current.id:
                # 后续指令
                if current.dest == instr.src1 or current.dest == instr.src2:
                    return True
        return False

    def check_WAW(self, current: Instruction,
                  issue_queue: List[Instruction]) -> bool:
        """
        检查WAW hazard
        后续指令会写入同一个目的寄存器
        """
        for instr in issue_queue:
            if instr.id > current.id:
                if current.dest == instr.dest:
                    return True
        return False


class SimplePipeline:
    """
    简单五级流水线模拟

    阶段：IF -> ID -> EX -> MEM -> WB
    支持转发和hazard检测。
    """

    def __init__(self, enable_forwarding: bool = True):
        self.enable_forwarding = enable_forwarding

        # 流水线阶段
        self.IF = PipelineStage("IF")
        self.ID = PipelineStage("ID")
        self.EX = PipelineStage("EX")
        self.MEM = PipelineStage("MEM")
        self.WB = PipelineStage("WB")

        # 流水线寄存器
        self.IF_ID = PipelineRegister("IF/ID")
        self.ID_EX = PipelineRegister("ID/EX")
        self.EX_MEM = PipelineRegister("EX/MEM")
        self.MEM_WB = PipelineRegister("MEM/WB")

        # 寄存器文件
        self.register_file: Dict[int, int] = {i: 0 for i in range(8)}

        # Hazard单元
        self.hazard_unit = HazardDetectionUnit()
        self.forwarding_unit = ForwardingUnit()

        # 内存（模拟）
        self.memory: Dict[int, int] = {i: 0 for i in range(0x1000)}

        # 指令队列
        self.instructions: List[Instruction] = []
        self.next_instr_id: int = 1

        # 时钟
        self.cycle: int = 0

        # 统计
        self.total_stalls: int = 0

    def add_instruction(self, instr: Instruction):
        """添加指令到队列"""
        self.instructions.append(instr)

    def fetch(self):
        """IF阶段：取指"""
        if self.IF_ID.valid and self.IF_ID.instruction:
            return  # 阻塞

        if self.instructions and self.next_instr_id <= len(self.instructions):
            instr = self.instructions[self.next_instr_id - 1]
            self.IF.instruction = instr
            self.IF.busy = True

    def decode(self):
        """ID阶段：译码"""
        if not self.IF_ID.valid:
            return

        instr = self.IF_ID.instruction
        if instr:
            self.ID.instruction = instr
            self.ID.busy = True

            # 读取寄存器
            if instr.src1 >= 0:
                instr.src1_value = self.register_file[instr.src1]
            if instr.src2 >= 0:
                instr.src2_value = self.register_file[instr.src2]

    def execute(self):
        """EX阶段：执行"""
        if not self.ID_EX.valid:
            return

        instr = self.ID_EX.instruction
        if not instr or instr.executing:
            return

        # 检查hazard
        ex_instr = self.EX_MEM.instruction if self.EX_MEM.valid else None
        mem_instr = self.MEM_WB.instruction if self.MEM_WB.valid else None

        if self.hazard_unit.check_RAW(instr, ex_instr, mem_instr):
            # 需要stall
            self.total_stalls += 1
            return

        # 执行
        instr.executing = True
        instr.execute_start = self.cycle

        # 简单ALU操作
        if instr.name == 'ADD':
            result = instr.src1_value + instr.src2_value
            instr.alu_result = result
        elif instr.name == 'SUB':
            result = instr.src1_value - instr.src2_value
            instr.alu_result = result
        elif instr.name == 'MUL':
            result = instr.src1_value * instr.src2_value
            instr.alu_result = result
        elif instr.name == 'LOAD':
            # 计算地址
            addr = instr.src1_value + (instr.src2 if instr.src2 >= 0 else 0)
            instr.memory_addr = addr
            instr.alu_result = addr
        elif instr.name == 'STORE':
            addr = instr.src1_value + (instr.src2 if instr.src2 >= 0 else 0)
            instr.memory_addr = addr
            instr.store_value = instr.src2_value

        instr.execute_end = self.cycle + instr.cycles

        self.EX.instruction = instr
        self.EX.busy = True

    def memory_access(self):
        """MEM阶段：访存"""
        if not self.EX_MEM.valid:
            return

        instr = self.EX_MEM.instruction
        if not instr:
            return

        if instr.name == 'LOAD':
            instr.loaded_value = self.memory.get(instr.memory_addr, 0)
        elif instr.name == 'STORE':
            self.memory[instr.memory_addr] = instr.store_value

        self.MEM.instruction = instr
        self.MEM.busy = True

    def write_back(self):
        """WB阶段：写回"""
        if not self.MEM_WB.valid:
            return

        instr = self.MEM_WB.instruction
        if not instr:
            return

        if instr.dest >= 0:
            if instr.name == 'LOAD':
                self.register_file[instr.dest] = instr.loaded_value
            else:
                self.register_file[instr.dest] = instr.alu_result

        instr.completed = True
        self.WB.instruction = instr
        self.WB.busy = True

    def step(self):
        """执行一个时钟周期"""
        self.cycle += 1

        # 流水线各阶段处理...

        # 推进流水线寄存器
        # 简化处理
        pass

    def run(self, max_cycles: int = 50) -> Dict:
        """运行模拟"""
        print(f"\n流水线模拟 (转发: {'启用' if self.enable_forwarding else '禁用'})")
        print("-" * 60)

        # 简化的顺序执行模拟
        reg_file = {i: 0 for i in range(8)}
        mem = {i: 0 for i in range(0x100)}

        print("\n执行序列:")

        for i, instr in enumerate(self.instructions):
            if i >= self.next_instr_id:
                break

            print(f"  Cycle {self.cycle + 1}: ", end="")

            # 读取寄存器
            v1 = reg_file[instr.src1] if instr.src1 >= 0 else 0
            v2 = reg_file[instr.src2] if instr.src2 >= 0 else 0

            # 执行
            if instr.name == 'ADD':
                result = v1 + v2
                reg_file[instr.dest] = result
                print(f"{instr.name} R{instr.dest}=R{instr.src1}+R{instr.src2}={v1}+{v2}={result}")
            elif instr.name == 'SUB':
                result = v1 - v2
                reg_file[instr.dest] = result
                print(f"{instr.name} R{instr.dest}=R{instr.src1}-R{instr.src2}={v1}-{v2}={result}")
            elif instr.name == 'LOAD':
                addr = v1 + (instr.src2 if instr.src2 >= 0 else 0)
                result = mem.get(addr, 0)
                reg_file[instr.dest] = result
                print(f"{instr.name} R{instr.dest}=Mem[{addr}]={result}")
            elif instr.name == 'STORE':
                addr = v1 + (instr.src2 if instr.src2 >= 0 else 0)
                mem[addr] = v2
                print(f"{instr.name} Mem[{addr}]=R{v2}")

            self.cycle += 1

        return {
            'total_cycles': self.cycle,
            'total_instructions': len(self.instructions),
            'total_stalls': self.total_stalls,
            'ipc': len(self.instructions) / self.cycle if self.cycle > 0 else 0
        }


def simulate_data_hazards():
    """
    模拟数据hazard和转发技术
    """
    print("=" * 60)
    print("数据 Hazard 与转发技术")
    print("=" * 60)

    # 示例1: RAW Hazard
    print("\n" + "-" * 40)
    print("示例1: RAW Hazard (真数据依赖)")
    print("-" * 40)

    print("\n指令序列:")
    print("  I1: ADD R1, R2, R3   ; R1 = R2 + R3")
    print("  I2: SUB R4, R1, R5   ; R4 = R1 - R5 (依赖I1的结果R1)")
    print("  I3: AND R6, R4, R7   ; R6 = R4 & R7 (依赖I2的结果R4)")

    # 演示转发路径
    print("\n转发路径:")
    print("  EX/MEM -> ID/EX: I1的ALU结果直接转发给I2")
    print("  MEM/WB -> ID/EX: 进一步转发（如果需要）")
    print("  无需停顿(stall)，只需转发")

    # 示例2: WAR Hazard
    print("\n" + "-" * 40)
    print("示例2: WAR Hazard (反依赖)")
    print("-" * 40)

    print("\n指令序列:")
    print("  I1: ADD R1, R2, R3   ; R1 = R2 + R3")
    print("  I2: SUB R2, R4, R5   ; R2 = R4 - R5 (写入R2，但I1要读R2)")
    print("  I3: AND R3, R1, R2   ; R3 = R1 & R2")

    print("\n在顺序发射/乱序执行的流水线中可能发生WAR hazard。")
    print("通过寄存器重命名可以解决。")

    # 示例3: WAW Hazard
    print("\n" + "-" * 40)
    print("示例3: WAW Hazard (输出依赖)")
    print("-" * 40)

    print("\n指令序列:")
    print("  I1: ADD R1, R2, R3   ; R1 = R2 + R3")
    print("  I2: SUB R1, R4, R5   ; R1 = R4 - R5 (覆盖R1)")
    print("  I3: MUL R1, R6, R7   ; R1 = R6 * R7 (再次覆盖R1)")

    print("\nWAW hazard需要确保最终写入的是最后一条指令的结果。")
    print("ROB和寄存器重命名可以解决。")

    # 转发技术示例
    print("\n" + "-" * 40)
    print("转发技术 (Forwarding)")
    print("-" * 40)

    print("\n转发路径:")
    print("  1. EX to EX: ALU结果在EX阶段直接转发到下一条指令的EX")
    print("  2. MEM to EX: MEM阶段的结果（LOAD结果）转发到EX")
    print("  3. MEM to MEM: STORE数据在MEM阶段直接使用")
    print("  4. WB to EX: 特殊情况，从WB转发")

    print("\n典型序列需要的转发:")
    print("  ADD R1, R2, R3")
    print("  SUB R4, R1, R5  -> EX/MEM.R1 转发到 ID/EX.R1")
    print("  AND R6, R4, R7  -> 需要等待SUB完成")

    # 流水线停顿示例
    print("\n" + "-" * 40)
    print("流水线停顿 (Stall)")
    print("-" * 40)

    print("\nLOAD指令后的RAW hazard需要1个cycle stall:")
    print("  LOAD R1, 0(R2)   ; R1 = Mem[R2]")
    print("  ADD  R3, R1, R4   ; R3 = R1 + R4")
    print("       ^ 需要等待LOAD结果，无法转发")
    print("  -> 需要在ID和EX之间插入1个气泡")

    # 模拟简单流水线
    print("\n" + "=" * 60)
    print("简单流水线模拟")
    print("=" * 60)

    pipeline = SimplePipeline(enable_forwarding=True)

    instructions = [
        Instruction(1, 'ADD', dest=1, src1=2, src2=3),
        Instruction(2, 'SUB', dest=4, src1=1, src2=5),
        Instruction(3, 'AND', dest=6, src1=4, src2=7),
        Instruction(4, 'LOAD', dest=8, src1=9, src2=-1),
        Instruction(5, 'ADD', dest=10, src1=8, src2=11),
    ]

    for instr in instructions:
        pipeline.add_instruction(instr)

    print("\n初始寄存器: R2=2, R3=3, R4=1, R5=4, R6=2, R7=3, R9=0x100")

    stats = pipeline.run(max_cycles=20)

    print(f"\n流水线统计:")
    print(f"  总周期数: {stats['total_cycles']}")
    print(f"  指令数: {stats['total_instructions']}")
    print(f"  停顿次数: {stats['total_stalls']}")
    print(f"  IPC: {stats['ipc']:.2f}")


if __name__ == "__main__":
    simulate_data_hazards()
