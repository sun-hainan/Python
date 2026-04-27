# -*- coding: utf-8 -*-

"""

算法实现：计算机体系结构_2 / pipeline_stall



本文件实现 pipeline_stall 相关的算法功能。

"""



import random

from typing import List, Optional, Dict, Set, Tuple

from dataclasses import dataclass, field

from enum import Enum, auto





class Stall_Reason(Enum):

    """停顿原因"""

    NONE = auto()

    FETCH_BRANCH_MISPREDICT = auto()   # 取指分支预测失败

    DATA_DEPENDENCY = auto()            # 数据依赖

    STRUCTURAL = auto()                 # 结构冲突

    LOAD_LATENCY = auto()              # LOAD延迟

    ROB_FULL = auto()                   # ROB满

    RS_FULL = auto()                    # 预约站满

    REGISTER_STALL = auto()            # 寄存器停顿





@dataclass

class Pipeline_Stage:

    """流水线级"""

    name: str = ""

    busy: bool = False

    instruction: Optional[str] = None

    stalled: bool = False

    stall_reason: Stall_Reason = Stall_Reason.NONE





class Pipeline_Stall_Simulator:

    """流水线停顿模拟器"""

    def __init__(self, num_stages: int = 5, width: int = 2):

        self.num_stages = num_stages

        self.width = width

        # 流水线各级

        self.stages: List[Pipeline_Stage] = [

            Pipeline_Stage(name=f"Stage{i}") for i in range(num_stages)

        ]

        # 停顿计数器

        self.stall_count: Dict[Stall_Reason, int] = {

            reason: 0 for reason in Stall_Reason

        }

        self.total_cycles: int = 0

        self.bubble_count: int = 0





    def insert_bubble(self, stage_idx: int, reason: Stall_Reason = Stall_Reason.NONE):

        """在指定级插入气泡（停顿）"""

        if 0 <= stage_idx < self.num_stages:

            stage = self.stages[stage_idx]

            stage.stalled = True

            stage.stall_reason = reason

            self.stall_count[reason] += 1

            self.bubble_count += 1





    def clear_stall(self, stage_idx: int):

        """清除指定级的停顿"""

        if 0 <= stage_idx < self.num_stages:

            self.stages[stage_idx].stalled = False

            self.stages[stage_idx].stall_reason = Stall_Reason.NONE





    def simulate_branch_mispredict(self):

        """模拟分支预测失败导致的流水线刷新"""

        # 在IF和ID级插入气泡

        self.insert_bubble(0, Stall_Reason.FETCH_BRANCH_MISPREDICT)

        self.insert_bubble(1, Stall_Reason.FETCH_BRANCH_MISPREDICT)

        print(f"  [分支预测失败] 在IF/ID级插入气泡")





    def simulate_data_dependency_stall(self, from_stage: int, to_stage: int):

        """模拟数据依赖导致的停顿"""

        for i in range(from_stage, to_stage + 1):

            self.insert_bubble(i, Stall_Reason.DATA_DEPENDENCY)

        print(f"  [数据依赖] 在Stage{from_stage}-Stage{to_stage}插入气泡")





    def simulate_rob_full(self):

        """模拟ROB满导致的停顿"""

        self.insert_bubble(2, Stall_Reason.ROB_FULL)  # Issue阶段

        print(f"  [ROB满] 在Issue级插入气泡")





    def step(self):

        """执行一个周期"""

        self.total_cycles += 1

        # 清除已处理的气泡

        for stage in self.stages:

            if stage.stalled and random.random() < 0.3:  # 30%概率清除

                self.clear_stall(self.stages.index(stage))





class Scoreboard:

    """积分板（用于检测数据冒险）"""

    def __init__(self):

        # 目的寄存器 -> 指令ID（正在执行中）

        self.pending_writes: Dict[int, int] = {}

        # 寄存器使用状态

        self.reg_status: Dict[int, str] = {}  # "free", "pending", "busy"





    def set_pending(self, dest_reg: int, instr_id: int):

        """设置寄存器待写"""

        self.pending_writes[dest_reg] = instr_id

        self.reg_status[dest_reg] = "pending"





    def is_ready(self, src_reg: int) -> bool:

        """检查源寄存器是否就绪"""

        return self.reg_status.get(src_reg, "free") == "free"





    def clear(self, dest_reg: int):

        """清除寄存器待写状态"""

        if dest_reg in self.pending_writes:

            del self.pending_writes[dest_reg]

        self.reg_status[dest_reg] = "free"





    def check_stall(self, instr_srcs: List[int], instr_id: int) -> Optional[Stall_Reason]:

        """检查指令是否需要停顿"""

        for src in instr_srcs:

            if not self.is_ready(src):

                return Stall_Reason.DATA_DEPENDENCY

        return None





class Pipeline_Simulator_With_Stalls:

    """带停顿的流水线模拟器"""

    def __init__(self):

        self.pipeline = Pipeline_Stall_Simulator(num_stages=5, width=2)

        self.scoreboard = Scoreboard()

        # 指令队列

        self.instruction_queue: List[str] = []

        # 统计

        self.cycles: int = 0

        self.instructions_completed: int = 0

        self.total_stalls: int = 0





    def fetch_instructions(self):

        """模拟取指"""

        # 随机生成一些指令

        for _ in range(self.pipeline.width):

            self.instruction_queue.append(f"INST_{random.randint(1000, 9999)}")





    def issue_instructions(self):

        """发射指令"""

        issued = 0

        for _ in range(self.pipeline.width):

            if not self.instruction_queue:

                break

            instr = self.instruction_queue.pop(0)

            # 检查数据依赖

            src_regs = [random.randint(0, 15) for _ in range(2)]

            stall_reason = self.scoreboard.check_stall(src_regs, 0)

            if stall_reason:

                # 需要停顿

                self.instruction_queue.insert(0, instr)  # 放回队列

                self.pipeline.insert_bubble(2, stall_reason)

                self.total_stalls += 1

                break

            # 发射成功

            dest_reg = random.randint(0, 15)

            self.scoreboard.set_pending(dest_reg, 0)

            print(f"  发射: {instr}, dest=r{dest_reg}")

            issued += 1





    def complete_instructions(self):

        """完成指令"""

        if random.random() < 0.3:  # 30%概率完成一条指令

            # 随机完成一个寄存器

            dest_reg = random.randint(0, 15)

            self.scoreboard.clear(dest_reg)

            self.instructions_completed += 1





    def run_cycle(self):

        """运行一个周期"""

        self.cycles += 1

        print(f"\nCycle {self.cycles}:")

        self.fetch_instructions()

        self.issue_instructions()

        self.complete_instructions()

        self.pipeline.step()





def basic_test():

    """基本功能测试"""

    print("=== 流水线停顿模拟器测试 ===")

    sim = Pipeline_Simulator_With_Stalls()

    print("\n流水线停顿场景演示:")

    # 场景1：分支预测失败

    print("\n[场景1] 分支预测失败")

    sim2 = Pipeline_Stall_Simulator()

    sim2.simulate_branch_mispredict()

    # 场景2：ROB满

    print("\n[场景2] ROB满")

    sim3 = Pipeline_Stall_Simulator()

    sim3.simulate_rob_full()

    # 场景3：数据依赖

    print("\n[场景3] 数据依赖")

    sim4 = Pipeline_Simulator_With_Stalls()

    print("\n运行10个周期:")

    for _ in range(10):

        sim4.run_cycle()

    print(f"\n最终统计:")

    print(f"  总周期: {sim4.cycles}")

    print(f"  完成指令: {sim4.instructions_completed}")

    print(f"  总停顿次数: {sim4.total_stalls}")

    print(f"  IPC: {sim4.instructions_completed / sim4.cycles:.2f}")





if __name__ == "__main__":

    basic_test()

