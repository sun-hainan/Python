# -*- coding: utf-8 -*-

"""

算法实现：编译器内核 / codegen



本文件实现 codegen 相关的算法功能。

"""



from typing import List, Dict, Set, Tuple, Optional, Any

from dataclasses import dataclass, field

from enum import Enum, auto

import heapq



# ========== 指令定义 ==========



@dataclass

class Instruction:

    """指令"""

    id: int

    opcode: str

    result: Optional[str] = None

    args: List[str] = field(default_factory=list)

    latency: int = 1  # 延迟周期

    issue_time: int = 0  # 发射时间

    finish_time: int = 0  # 完成时间

    

    def __repr__(self):

        return f"Inst({self.id}, {self.opcode}, issue={self.issue_time})"





@dataclass

class Resource:

    """资源（执行单元）"""

    name: str

    busy_until: int = 0  # 忙碌到的时间

    

    def is_available(self, time: int) -> bool:

        return self.busy_until <= time





@dataclass

class Dependence:

    """依赖关系"""

    from_inst: int

    to_inst: int

    latency: int = 1  # 依赖延迟





# ========== List Scheduling ==========



class ListScheduler:

    """

    List Scheduling（列表调度）算法

    简单高效的任务调度算法

    """

    

    def __init__(self, instructions: List[Instruction], 

                 dependencies: List[Dependence]):

        self.instructions = instructions

        self.dependencies = dependencies

        self.ready_queue: List[Instruction] = []  # 就绪指令队列

        self.scheduled: Set[int] = set()

        self.current_time = 0

        self.dep_graph: Dict[int, Set[int]] = {}  # inst -> 依赖的inst

        

        # 构建依赖图

        self._build_dep_graph()

    

    def _build_dep_graph(self):

        """构建依赖图"""

        for dep in self.dependencies:

            if dep.to_inst not in self.dep_graph:

                self.dep_graph[dep.to_inst] = set()

            self.dep_graph[dep.to_inst].add(dep.from_inst)

    

    def schedule(self) -> List[Instruction]:

        """

        执行List Scheduling

        返回: 调度后的指令列表

        """

        # 初始化就绪队列

        for instr in self.instructions:

            if instr.id not in self.dep_graph or not self.dep_graph[instr.id]:

                heapq.heappush(self.ready_queue, (0, instr.id))

        

        scheduled_insts = {}

        

        while self.ready_queue:

            # 选择优先级最高的就绪指令

            priority, instr_id = heapq.heappop(self.ready_queue)

            

            if instr_id in self.scheduled:

                continue

            

            instr = self.instructions[instr_id]

            

            # 计算最早可能的时间

            earliest_time = self._compute_earliest_time(instr)

            

            # 调度指令

            instr.issue_time = earliest_time

            instr.finish_time = earliest_time + instr.latency

            

            scheduled_insts[instr.id] = instr

            self.scheduled.add(instr.id)

            

            # 更新后继指令

            self._update_successors(instr)

        

        return list(scheduled_insts.values())

    

    def _compute_earliest_time(self, instr: Instruction) -> int:

        """计算最早可能发射时间"""

        earliest = self.current_time

        

        # 考虑依赖

        deps = self.dep_graph.get(instr.id, set())

        for dep_id in deps:

            if dep_id in self.scheduled:

                # 找到发射的指令

                dep_instr = scheduled_insts.get(dep_id) if 'scheduled_insts' in dir() else None

                if dep_instr:

                    earliest = max(earliest, dep_instr.finish_time)

        

        return earliest

    

    def _update_successors(self, instr: Instruction):

        """更新后继指令"""

        # 找到以instr为前驱的依赖

        for dep in self.dependencies:

            if dep.from_inst == instr.id:

                # 检查是否所有前驱都已完成

                if self._all_deps_satisfied(dep.to_inst):

                    target_instr = self.instructions[dep.to_inst]

                    priority = self._compute_priority(target_instr)

                    heapq.heappush(self.ready_queue, (priority, dep.to_inst))

    

    def _all_deps_satisfied(self, instr_id: int) -> bool:

        """检查是否所有依赖都满足"""

        deps = self.dep_graph.get(instr_id, set())

        return deps.issubset(self.scheduled)

    

    def _compute_priority(self, instr: Instruction) -> int:

        """计算指令优先级（路径长度）"""

        # 简化为逆拓扑顺序

        return -len(self._get_successor_depth(instr.id))

    

    def _get_successor_depth(self, instr_id: int) -> int:

        """计算后续深度"""

        max_depth = 0

        for dep in self.dependencies:

            if dep.from_inst == instr_id:

                depth = self._get_successor_depth(dep.to_inst)

                max_depth = max(max_depth, depth + 1)

        return max_depth





# ========== 带资源的List Scheduling ==========



class ResourceAwareScheduler(ListScheduler):

    """

    资源感知的List Scheduling

    考虑执行单元的有限资源

    """

    

    def __init__(self, instructions: List[Instruction],

                 dependencies: List[Dependence],

                 resources: List[Resource]):

        super().__init__(instructions, dependencies)

        self.resources = resources

    

    def schedule(self) -> List[Instruction]:

        """带资源约束的调度"""

        scheduled_insts = {}

        

        # 初始化就绪队列

        for instr in self.instructions:

            if instr.id not in self.dep_graph or not self.dep_graph[instr.id]:

                heapq.heappush(self.ready_queue, (0, instr.id))

        

        while self.ready_queue:

            priority, instr_id = heapq.heappop(self.ready_queue)

            

            if instr_id in self.scheduled:

                continue

            

            instr = self.instructions[instr_id]

            

            # 计算最早可用资源时间

            earliest_time = self._compute_earliest_time(instr)

            

            # 找到第一个可用资源

            resource_time = self._find_available_resource_time(instr, earliest_time)

            

            schedule_time = max(earliest_time, resource_time)

            

            instr.issue_time = schedule_time

            instr.finish_time = schedule_time + instr.latency

            

            # 占用资源

            self._occupy_resource(instr, schedule_time)

            

            scheduled_insts[instr.id] = instr

            self.scheduled.add(instr.id)

            

            self._update_successors(instr)

        

        return list(scheduled_insts.values())

    

    def _find_available_resource_time(self, instr: Instruction, 

                                     earliest: int) -> int:

        """找到第一个可用资源的时间"""

        # 简化：只使用第一个资源

        res = self.resources[0] if self.resources else None

        if res:

            return max(earliest, res.busy_until)

        return earliest

    

    def _occupy_resource(self, instr: Instruction, time: int):

        """占用资源"""

        if self.resources:

            self.resources[0].busy_until = time + instr.latency





# ========== DAG调度 ==========



class DAGScheduler:

    """

    DAG调度器

    基于依赖DAG的调度

    """

    

    def __init__(self):

        self.ready_list: List[Tuple[int, int]] = []  # (priority, inst_id)

        self.scheduled: Set[int] = set()

        self.earliest_start: Dict[int, int] = {}

    

    def schedule_dag(self, dag: List[Instruction], 

                    dependencies: List[Dependence]) -> List[Instruction]:

        """

        调度DAG

        """

        # 构建后继映射

        successors: Dict[int, List[int]] = {}

        for dep in dependencies:

            if dep.from_inst not in successors:

                successors[dep.from_inst] = []

            successors[dep.from_inst].append(dep.to_inst)

        

        # 找到入度为0的节点

        in_degree = {}

        for instr in dag:

            in_degree[instr.id] = 0

        

        for dep in dependencies:

            in_degree[dep.to_inst] += 1

        

        for instr in dag:

            if in_degree[instr.id] == 0:

                heapq.heappush(self.ready_list, (0, instr.id))

        

        result = []

        

        while self.ready_list:

            priority, instr_id = heapq.heappop(self.ready_list)

            

            if instr_id in self.scheduled:

                continue

            

            instr = dag[instr_id]

            

            # 计算最早开始时间

            start_time = self._get_earliest_start(instr, successors)

            instr.issue_time = start_time

            instr.finish_time = start_time + instr.latency

            

            result.append(instr)

            self.scheduled.add(instr_id)

            

            # 添加就绪的后继

            for succ_id in successors.get(instr_id, []):

                if all(dep.from_inst in self.scheduled for dep in dependencies 

                      if dep.to_inst == succ_id):

                    heapq.heappush(self.ready_list, (self._compute_priority(succ_id), succ_id))

        

        return result

    

    def _get_earliest_start(self, instr: Instruction, 

                           successors: Dict[int, List[int]]) -> int:

        """获取最早开始时间"""

        return self.earliest_start.get(instr.id, 0)

    

    def _compute_priority(self, instr_id: int) -> int:

        """计算优先级"""

        return 0





# ========== 寄存器分配后调度 ==========



class PostRegAllocScheduler:

    """

    寄存器分配后的指令调度

    处理寄存器溢出

    """

    

    def __init__(self, instructions: List[Instruction]):

        self.instructions = instructions

    

    def schedule(self) -> List[Instruction]:

        """调度已分配寄存器的指令"""

        scheduled = []

        

        pending_loads: List[Instruction] = []

        pending_stores: List[Instruction] = []

        

        for instr in self.instructions:

            # 检查是否需要加载

            if self._needs_load(instr):

                # 插入加载指令

                load = self._create_load(instr)

                heapq.heappush(pending_loads, (instr.issue_time, load))

            

            # 检查是否可以直接发射

            if self._can_issue(instr, pending_loads):

                scheduled.append(instr)

            else:

                # 延迟发射

                instr.issue_time += 1

                scheduled.append(instr)

            

            # 处理存储

            if self._needs_store(instr):

                store = self._create_store(instr)

                heapq.heappush(pending_stores, (instr.issue_time + instr.latency, store))

        

        # 添加所有待处理的存储

        for _, store in pending_stores:

            scheduled.append(store)

        

        return scheduled

    

    def _needs_load(self, instr: Instruction) -> bool:

        """检查是否需要加载"""

        return False

    

    def _needs_store(self, instr: Instruction) -> bool:

        """检查是否需要存储"""

        return False

    

    def _can_issue(self, instr: Instruction, pending_loads: List) -> bool:

        """检查是否可以发射"""

        return True

    

    def _create_load(self, instr: Instruction) -> Instruction:

        """创建加载指令"""

        return instr

    

    def _create_store(self, instr: Instruction) -> Instruction:

        """创建存储指令"""

        return instr





if __name__ == "__main__":

    print("=" * 60)

    print("指令调度（List Scheduling）演示")

    print("=" * 60)

    

    # 创建测试指令

    instructions = [

        Instruction(0, "add", result="t0", args=["a", "b"], latency=1),

        Instruction(1, "mul", result="t1", args=["t0", "c"], latency=2),

        Instruction(2, "sub", result="t2", args=["t0", "d"], latency=1),

        Instruction(3, "add", result="t3", args=["t1", "t2"], latency=1),

    ]

    

    # 创建依赖关系

    dependencies = [

        Dependence(from_inst=0, to_inst=1, latency=1),

        Dependence(from_inst=0, to_inst=2, latency=1),

        Dependence(from_inst=1, to_inst=3, latency=1),

        Dependence(from_inst=2, to_inst=3, latency=1),

    ]

    

    print("\n--- 原始指令 ---")

    for instr in instructions:

        print(f"  {instr.id}: {instr.opcode} <- args={instr.args}")

    

    print("\n依赖关系:")

    for dep in dependencies:

        print(f"  {dep.from_inst} -> {dep.to_inst} (latency={dep.latency})")

    

    # 执行调度

    print("\n--- List Scheduling ---")

    scheduler = ListScheduler(instructions, dependencies)

    scheduled = scheduler.schedule()

    

    print("调度结果:")

    for instr in scheduled:

        print(f"  {instr.id}: {instr.opcode} @ time={instr.issue_time} (finish={instr.finish_time})")

    

    # 资源感知调度

    print("\n--- 资源感知调度 ---")

    resources = [Resource("ALU1"), Resource("ALU2")]

    res_scheduler = ResourceAwareScheduler(instructions, dependencies, resources)

    scheduled_res = res_scheduler.schedule()

    

    print("调度结果（含资源）:")

    for instr in scheduled_res:

        print(f"  {instr.id}: {instr.opcode} @ time={instr.issue_time}")

    

    print("\n调度算法关键点:")

    print("  1. 维护就绪指令队列（优先级队列）")

    print("  2. 计算依赖约束的最早时间")

    print("  3. 选择最高优先级指令发射")

    print("  4. 更新后继的可用性")

    print("  5. 资源约束时寻找可用资源")

