# -*- coding: utf-8 -*-

"""

算法实现：编译器优化 / instruction_scheduling



本文件实现 instruction_scheduling 相关的算法功能。

"""



from typing import List, Dict, Set, Optional, Tuple

from collections import defaultdict, deque

import random





class Instruction:

    """指令"""

    def __init__(self, id: int, op: str, dest: Optional[str], 

                 src1: Optional[str] = None, src2: Optional[str] = None,

                 latency: int = 1):

        self.id = id

        self.op = op

        self.dest = dest

        self.src1 = src1

        self.src2 = src2

        self.latency = latency

        

        # 调度信息

        self.ready_time = 0

        self.scheduled_time = None

        self.unscheduled = True

    

    def uses(self) -> Set[str]:

        """使用的寄存器"""

        result = set()

        if self.src1:

            result.add(self.src1)

        if self.src2:

            result.add(self.src2)

        return result

    

    def defines(self) -> Set[str]:

        """定义的寄存器"""

        if self.dest:

            return {self.dest}

        return set()

    

    def __repr__(self):

        if self.dest:

            return f"{self.id}: {self.dest} = {self.op} {self.src1} {self.src2 or ''}"

        return f"{self.id}: {self.op} {self.src1} {self.src2 or ''}"





class Register:

    """寄存器"""

    def __init__(self, name: str):

        self.name = name

        self.current_value = None

        self.uses = []  # 使用这个值的指令

    

    def is_available(self, time: int) -> bool:

        """检查寄存器在给定时间是否可用"""

        # 简化:假设所有寄存器可用

        return True





class InstructionScheduler:

    """

    指令调度器

    使用列表调度算法

    """

    

    def __init__(self, instructions: List[Instruction], num_resources: int = 1):

        """

        初始化

        

        Args:

            instructions: 指令列表

            num_resources: 功能单元数量

        """

        self.instructions = instructions

        self.num_resources = num_resources

        self.schedule = []

        

        # 构建依赖图

        self._build_dependency_graph()

    

    def _build_dependency_graph(self):

        """构建数据依赖图"""

        self.deps = defaultdict(list)  # {instr_id: [dependent_ids]}

        self.rev_deps = defaultdict(list)  # {instr_id: [prereq_ids]}

        

        # 跟踪每个变量的最近定义位置

        last_def = {}

        

        for instr in self.instructions:

            # 检查数据依赖

            for var in instr.uses():

                if var in last_def:

                    prereq_id = last_def[var]

                    self.deps[prereq_id].append(instr.id)

                    self.rev_deps[instr.id].append(prereq_id)

            

            # 更新最后定义

            for var in instr.defines():

                last_def[var] = instr.id

    

    def compute_priorities(self) -> Dict[int, int]:

        """

        计算每条指令的优先级(到叶子的最长路径)

        

        Returns:

            {instr_id: priority}

        """

        # 使用递归计算

        memo = {}

        

        def longest_path(id: int) -> int:

            if id in memo:

                return memo[id]

            

            successors = self.deps.get(id, [])

            if not successors:

                memo[id] = 1

            else:

                memo[id] = 1 + max(longest_path(s) for s in successors)

            

            return memo[id]

        

        priorities = {}

        for instr in self.instructions:

            priorities[instr.id] = longest_path(instr.id)

        

        return priorities

    

    def list_schedule(self) -> List[Tuple[int, int]]:

        """

        列表调度算法

        

        Returns:

            [(instr_id, scheduled_time), ...]

        """

        priorities = self.compute_priorities()

        

        # 初始化就绪队列

        ready = []

        scheduled = set()

        

        # 找出所有没有前驱的指令

        for instr in self.instructions:

            if not self.rev_deps[instr.id]:

                ready.append(instr.id)

        

        # 按优先级排序(高的先调度)

        ready.sort(key=lambda id: -priorities[id])

        

        schedule_time = 0

        scheduled_instrs = []

        

        while len(scheduled) < len(self.instructions):

            # 如果就绪队列为空,时间前移到下一个就绪

            if not ready:

                # 找到下一个应该就绪的指令

                min_ready_time = float('inf')

                for instr in self.instructions:

                    if instr.id not in scheduled:

                        # 检查所有前驱是否已调度

                        all_done = all(pid in scheduled for pid in self.rev_deps[instr.id])

                        if all_done:

                            min_ready_time = min(min_ready_time, instr.ready_time)

                

                schedule_time = max(schedule_time, min_ready_time)

                ready = [instr.id for instr in self.instructions 

                        if instr.id not in scheduled 

                        and all(pid in scheduled for pid in self.rev_deps[instr.id])]

                ready.sort(key=lambda id: -priorities[id])

                continue

            

            # 调度指令

            scheduled_count = 0

            while ready and scheduled_count < self.num_resources:

                instr_id = ready.pop(0)

                

                # 检查资源冲突(简化:无冲突)

                # 检查是否有其他指令在同一时间使用相同功能单元

                

                # 调度

                scheduled_instrs.append((instr_id, schedule_time))

                scheduled.add(instr_id)

                scheduled_count += 1

                

                # 更新后继指令的ready_time

                for succ_id in self.deps[instr_id]:

                    # 检查所有前驱是否已调度

                    all_done = all(pid in scheduled for pid in self.rev_deps[succ_id])

                    if all_done:

                        succ = self.instructions[succ_id]

                        # 计算就绪时间 = max(所有前驱完成时间) + latency

                        max_finish = schedule_time

                        for pid in self.rev_deps[succ_id]:

                            for sid, st in scheduled_instrs:

                                if sid == pid:

                                    max_finish = max(max_finish, st + self.instructions[pid].latency)

                                    break

                        succ.ready_time = max_finish

                        

                        if succ not in ready:

                            ready.append(succ_id)

                            ready.sort(key=lambda id: -priorities[id])

            

            schedule_time += 1

        

        return scheduled_instrs

    

    def compute_stalls(self, schedule: List[Tuple[int, int]]) -> int:

        """

        计算调度后的停顿数

        

        Args:

            schedule: 调度结果

        

        Returns:

            停顿次数

        """

        total_stalls = 0

        last_scheduled = {}

        

        for instr_id, time in schedule:

            instr = self.instructions[instr_id]

            

            # 计算数据依赖导致的停顿

            for prereq_id in self.rev_deps[instr_id]:

                if prereq_id in last_scheduled:

                    prereq_time = last_scheduled[prereq_id]

                    prereq_finish = prereq_time + self.instructions[prereq_id].latency

                    

                    if prereq_finish > time:

                        total_stalls += prereq_finish - time

            

            last_scheduled[instr_id] = time

        

        return total_stalls





def schedule_instructions(instructions: List[Tuple], 

                         num_resources: int = 1) -> List[Tuple[int, int]]:

    """

    指令调度便捷函数

    

    Args:

        instructions: [(op, dest, src1, src2), ...]

        num_resources: 功能单元数

    

    Returns:

        [(instr_id, time), ...]

    """

    instrs = []

    for i, (op, dest, src1, src2) in enumerate(instructions):

        instrs.append(Instruction(i, op, dest, src1, src2))

    

    scheduler = InstructionScheduler(instrs, num_resources)

    return scheduler.list_schedule()





# 测试代码

if __name__ == "__main__":

    # 测试1: 简单指令序列

    print("测试1 - 简单指令序列:")

    

    # 指令:

    # 0: a = b + c  (latency=1)

    # 1: d = a + e  (依赖于0)

    # 2: f = d + g  (依赖于1)

    

    instructions = [

        Instruction(0, 'ADD', 'a', 'b', 'c'),

        Instruction(1, 'ADD', 'd', 'a', 'e'),

        Instruction(2, 'ADD', 'f', 'd', 'g'),

    ]

    

    scheduler = InstructionScheduler(instructions)

    schedule = scheduler.list_schedule()

    

    print(f"  指令: {[str(i) for i in instructions]}")

    print(f"  调度: {schedule}")

    print(f"  停顿: {scheduler.compute_stalls(schedule)}")

    

    # 测试2: 无依赖指令

    print("\n测试2 - 无依赖指令(可并行):")

    

    instructions2 = [

        Instruction(0, 'ADD', 'a', 'b', 'c'),

        Instruction(1, 'ADD', 'd', 'e', 'f'),

        Instruction(2, 'ADD', 'g', 'h', 'i'),

    ]

    

    scheduler2 = InstructionScheduler(instructions2, num_resources=3)

    schedule2 = scheduler2.list_schedule()

    

    print(f"  调度: {schedule2}")

    print(f"  总时间: {max(t for _, t in schedule2) + 1}")

    

    # 测试3: 复杂依赖图

    print("\n测试3 - 复杂依赖图:")

    

    # a = b + c

    # d = a + 1

    # e = a - 1

    # f = d + e

    # g = f + 1

    

    instructions3 = [

        Instruction(0, 'ADD', 'a', 'b', 'c'),

        Instruction(1, 'ADD', 'd', 'a', '1'),

        Instruction(2, 'SUB', 'e', 'a', '1'),

        Instruction(3, 'ADD', 'f', 'd', 'e'),

        Instruction(4, 'ADD', 'g', 'f', '1'),

    ]

    

    scheduler3 = InstructionScheduler(instructions3)

    schedule3 = scheduler3.list_schedule()

    

    print(f"  调度: {schedule3}")

    

    # 测试4: 寄存器分配

    print("\n测试4 - 不同资源数:")

    

    for num_res in [1, 2, 3]:

        scheduler_res = InstructionScheduler(instructions3, num_resources=num_res)

        schedule_res = scheduler_res.list_schedule()

        makespan = max(t for _, t in schedule_res) + 1

        print(f"  资源数={num_res}: 总时间={makespan}")

    

    # 测试5: 优先级效果

    print("\n测试5 - 优先级分析:")

    

    priorities = scheduler3.compute_priorities()

    print(f"  指令优先级: {priorities}")

    

    # 测试6: 模拟实际流水线

    print("\n测试6 - 流水线调度:")

    

    # 模拟5级流水线

    # 每个指令需要5个周期完成

    

    for i, instr in enumerate(instructions3):

        instr.latency = 5

    

    scheduler_pipe = InstructionScheduler(instructions3, num_resources=2)

    schedule_pipe = scheduler_pipe.list_schedule()

    

    print(f"  流水线调度(2个FU, latency=5):")

    for instr_id, time in schedule_pipe:

        finish = time + instructions3[instr_id].latency

        print(f"    指令{instr_id}: 开始={time}, 结束={finish}")

    

    print(f"  总周期数: {max(t + instructions3[i].latency for i, t in schedule_pipe)}")

    

    print("\n所有测试完成!")

