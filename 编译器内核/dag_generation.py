# -*- coding: utf-8 -*-

"""

算法实现：编译器内核 / dag_generation



本文件实现 dag_generation 相关的算法功能。

"""



from typing import List, Dict, Set, Optional, Tuple

from dataclasses import dataclass, field

from enum import Enum

import heapq





# =============================================================================

# 数据结构定义

# =============================================================================



@dataclass

class ResourceUnit:

    """资源单元：代表一个功能单元（如 ALU、LOAD/STORE 单元）"""

    name: str  # 资源名称

    latency: int  # 延迟周期数



    def __repr__(self):

        return f"Resource({self.name}, latency={self.latency})"





@dataclass

class SchedInstruction:

    """

    可调度指令



    包含指令信息和调度相关属性

    """

    id: int  # 指令唯一ID

    opcode: str  # 操作码

    src_regs: List[str] = field(default_factory=list)  # 源寄存器

    dst_regs: List[str] = field(default_factory=list)  # 目标寄存器

    resources: List[str] = field(default_factory=list)  # 需要的资源类型

    latency: int = 1  # 执行延迟（周期数）

    label: str = ""  # 调试标签



    def __repr__(self):

        return f"Inst[{self.id}]({self.opcode})"





@dataclass

class DependenceEdge:

    """依赖边：表示两条指令之间的依赖关系"""

    from_id: int  # 源指令ID

    to_id: int  # 目标指令ID

    distance: int = 1  # 最小距离（周期数）



    def __repr__(self):

        return f"Edge({self.from_id} -> {self.to_id}, dist={self.distance})"





# =============================================================================

# 指令调度DAG

# =============================================================================



class InstructionSchedulingDAG:

    """

    指令调度DAG



    构建指令之间的依赖图，并生成调度序列



    依赖类型：

        1. 数据依赖（RAW）：真数据相关

        2. 反依赖（WAR）：先写后读

        3. 输出依赖（WAR）：先读后写

        4. 控制依赖：分支相关

    """



    def __init__(self):

        self.instructions: Dict[int, SchedInstruction] = {}  # 指令ID -> 指令

        self.edges: List[DependenceEdge] = []  # 依赖边列表

        self.adjacency: Dict[int, List[int]] = {}  # 出边表：节点ID -> [依赖节点ID列表]

        self.reverse_adj: Dict[int, List[int]] = {}  # 入边表

        self.resources: Dict[str, ResourceUnit] = {}  # 资源名称 -> 资源



        # 计算属性

        self.depths: Dict[int, int] = {}  # 关键路径深度（从叶节点开始）

        self.ranks: Dict[int, float] = {}  # 调度优先级（基于关键路径）



    def add_instruction(self, instr: SchedInstruction):

        """添加一条指令"""

        self.instructions[instr.id] = instr

        if instr.id not in self.adjacency:

            self.adjacency[instr.id] = []

        if instr.id not in self.reverse_adj:

            self.reverse_adj[instr.id] = []



    def add_resource(self, name: str, latency: int = 1):

        """添加一个资源单元"""

        self.resources[name] = ResourceUnit(name, latency)



    def add_dependence(self, from_id: int, to_id: int, distance: int = 1):

        """

        添加依赖边



        参数:

            from_id: 源指令ID（必须先执行）

            to_id: 目标指令ID（依赖于源指令）

            distance: 最小周期距离

        """

        if from_id not in self.instructions or to_id not in self.instructions:

            raise ValueError("指令ID不存在")



        edge = DependenceEdge(from_id, to_id, distance)

        self.edges.append(edge)



        self.adjacency.setdefault(from_id, []).append(to_id)

        self.reverse_adj.setdefault(to_id, []).append(from_id)



    def build_data_dependence(self):

        """基于寄存器自动构建数据依赖"""

        # 追踪每个寄存器的最后一条写入指令

        last_write: Dict[str, Tuple[int, str]] = {}  # 寄存器 -> (指令ID, 寄存器)



        for instr_id in sorted(self.instructions.keys()):

            instr = self.instructions[instr_id]



            # 检查读后写（WAR）和写后写（WAW）依赖

            for reg in instr.src_regs:

                if reg in last_write:

                    prev_id, _ = last_write[reg]

                    if prev_id != instr_id:

                        self.add_dep(prev_id, instr_id, distance=1)



            # 更新写寄存器信息

            for reg in instr.dst_regs:

                last_write[reg] = (instr_id, reg)



    def add_dep(self, from_id: int, to_id: int, distance: int = 1):

        """添加依赖的简写方法"""

        self.add_dep(from_id, to_id, distance)



    def compute_critical_path(self) -> int:

        """

        计算关键路径长度



        返回:

            关键路径长度（周期数）

        """

        # 拓扑排序

        in_degree = {i: len(self.reverse_adj.get(i, [])) for i in self.instructions}

        ready = [i for i, d in in_degree.items() if d == 0]



        # 按拓扑序计算每个节点的最大深度

        while ready:

            node_id = ready.pop(0)

            instr = self.instructions[node_id]



            # 深度 = max(所有前驱深度 + 延迟) + 当前指令延迟

            max_pred_depth = 0

            for pred_id in self.reverse_adj.get(node_id, []):

                edge = self._find_edge(pred_id, node_id)

                dist = edge.distance if edge else 1

                max_pred_depth = max(max_pred_depth, self.depths[pred_id] + dist)



            self.depths[node_id] = max(max_pred_depth + instr.latency, instr.latency)



            # 更新后继节点的入度

            for succ_id in self.adjacency.get(node_id, []):

                in_degree[succ_id] -= 1

                if in_degree[succ_id] == 0:

                    ready.append(succ_id)



        # 关键路径 = 最大深度

        return max(self.depths.values()) if self.depths else 0



    def _find_edge(self, from_id: int, to_id: int) -> Optional[DependenceEdge]:

        """查找从 from_id 到 to_id 的边"""

        for edge in self.edges:

            if edge.from_id == from_id and edge.to_id == to_id:

                return edge

        return None



    def compute_ranks(self):

        """计算调度优先级（基于关键路径的逆序排名）"""

        critical_path = self.compute_critical_path()



        # 计算每个节点的 rank（到终点的估计距离）

        for instr_id in self.instructions:

            if instr_id not in self.depths:

                continue

            # rank = 深度 + 估算剩余距离

            self.ranks[instr_id] = float(critical_path - self.depths[instr_id] + self.instructions[instr_id].latency)



    def topological_sort(self) -> List[int]:

        """

        拓扑排序获取合法调度顺序



        返回:

            指令ID的拓扑序列表

        """

        in_degree = {i: len(self.reverse_adj.get(i, [])) for i in self.instructions}

        result = []

        queue = [i for i, d in in_degree.items() if d == 0]



        while queue:

            node_id = queue.pop(0)

            result.append(node_id)



            for succ_id in self.adjacency.get(node_id, []):

                in_degree[succ_id] -= 1

                if in_degree[succ_id] == 0:

                    queue.append(succ_id)



        return result



    def list_schedule(self, issue_width: int = 1) -> Dict[int, int]:

        """

        列表调度（List Scheduling）算法



        参数:

            issue_width: 每周期可以发射的指令数



        返回:

            调度表：指令ID -> 发射周期

        """

        self.compute_ranks()



        # 初始化

        schedule: Dict[int, int] = {}  # 指令ID -> 发射周期

        ready_list: List[Tuple[float, int]] = []  # (优先级, 指令ID)

        current_cycle = 0



        # 追踪每条指令的完成时间（考虑延迟）

        finish_time: Dict[int, int] = {}

        in_degree = {i: len(self.reverse_adj.get(i, [])) for i in self.instructions}

        all_scheduled = set()



        # 初始就绪队列

        for instr_id in self.instructions:

            if in_degree[instr_id] == 0:

                heapq.heappush(ready_list, (-self.ranks[instr_id], instr_id))



        while all_scheduled != set(self.instructions.keys()):

            # 当前周期可以发射的指令

            issued_this_cycle = 0



            while ready_list and issued_this_cycle < issue_width:

                _, instr_id = heapq.heappop(ready_list)



                if instr_id in all_scheduled:

                    continue



                # 检查资源是否可用（简化版：跳过资源检查）

                # 检查依赖是否满足（所有前驱已完成）

                can_issue = True

                for pred_id in self.reverse_adj.get(instr_id, []):

                    edge = self._find_edge(pred_id, instr_id)

                    dist = edge.distance if edge else 1

                    if finish_time.get(pred_id, 0) + dist > current_cycle:

                        can_issue = False

                        break



                if can_issue:

                    schedule[instr_id] = current_cycle

                    finish_time[instr_id] = current_cycle + self.instructions[instr_id].latency

                    all_scheduled.add(instr_id)

                    issued_this_cycle += 1



                    # 将后继加入就绪队列

                    for succ_id in self.adjacency.get(instr_id, []):

                        in_degree[succ_id] -= 1

                        if in_degree[succ_id] == 0 and succ_id not in all_scheduled:

                            heapq.heappush(ready_list, (-self.ranks[succ_id], succ_id))



            current_cycle += 1



        return schedule





# =============================================================================

# 调度结果分析

# =============================================================================



class ScheduleAnalyzer:

    """调度结果分析器"""



    @staticmethod

    def compute_schedule_length(schedule: Dict[int, int], instructions: Dict[int, SchedInstruction]) -> int:

        """计算调度后的总周期数"""

        if not schedule:

            return 0

        max_cycle = 0

        for instr_id, cycle in schedule.items():

            instr = instructions[instr_id]

            end_cycle = cycle + instr.latency

            max_cycle = max(max_cycle, end_cycle)

        return max_cycle



    @staticmethod

    def print_schedule(schedule: Dict[int, int], instructions: Dict[int, SchedInstruction]):

        """打印调度结果"""

        print("\n调度表:")

        print("-" * 40)

        print(f"{'Cycle':<8} {'InstID':<8} {'Opcode':<12} {'Label'}")

        print("-" * 40)



        for instr_id in sorted(schedule.keys(), key=lambda x: schedule[x]):

            cycle = schedule[instr_id]

            instr = instructions[instr_id]

            print(f"{cycle:<8} {instr_id:<8} {instr.opcode:<12} {instr.label}")



        length = ScheduleAnalyzer.compute_schedule_length(schedule, instructions)

        print("-" * 40)

        print(f"总周期数: {length}")





# =============================================================================

# 测试代码

# =============================================================================



if __name__ == "__main__":

    print("=" * 60)

    print("指令调度DAG测试")

    print("=" * 60)



    # 创建指令调度DAG

    dag = InstructionSchedulingDAG()



    # 添加资源

    dag.add_resource("ALU", latency=1)

    dag.add_resource("LOAD", latency=2)

    dag.add_resource("STORE", latency=1)



    # 添加测试指令

    instructions = [

        SchedInstruction(0, "LOAD", [], ["r1"], ["LOAD"], latency=2, label="r1 = mem[a]"),

        SchedInstruction(1, "LOAD", [], ["r2"], ["LOAD"], latency=2, label="r2 = mem[b]"),

        SchedInstruction(2, "ADD", ["r1", "r2"], ["r3"], ["ALU"], latency=1, label="r3 = r1 + r2"),

        SchedInstruction(3, "ADD", ["r3", "r1"], ["r4"], ["ALU"], latency=1, label="r4 = r3 + r1"),

        SchedInstruction(4, "STORE", ["r4"], [], ["STORE"], latency=1, label="mem[c] = r4"),

    ]



    for instr in instructions:

        dag.add_instruction(instr)



    # 添加数据依赖

    dag.add_dep(0, 2)  # r1 用于 ADD

    dag.add_dep(1, 2)  # r2 用于 ADD

    dag.add_dep(2, 3)  # r3 用于 ADD

    dag.add_dep(3, 4)  # r4 用于 STORE



    print("\n【测试1：拓扑排序】")

    topo_order = dag.topological_sort()

    print(f"拓扑序: {topo_order}")



    print("\n【测试2：关键路径计算】")

    cp_length = dag.compute_critical_path()

    print(f"关键路径长度: {cp_length} 周期")



    print("\n【测试3：列表调度】")

    schedule = dag.list_schedule(issue_width=2)

    analyzer = ScheduleAnalyzer()

    analyzer.print_schedule(schedule, dag.instructions)



    print("\n【测试4：资源约束调度】")

    # 重新创建DAG模拟更复杂的场景

    dag2 = InstructionSchedulingDAG()

    dag2.add_resource("ALU", latency=1)



    instructions2 = [

        SchedInstruction(0, "ADD", ["x1", "x2"], ["y1"], ["ALU"], label="y1 = x1 + x2"),

        SchedInstruction(1, "ADD", ["x3", "x4"], ["y2"], ["ALU"], label="y2 = x3 + x4"),

        SchedInstruction(2, "ADD", ["y1", "y2"], ["z"], ["ALU"], label="z = y1 + y2"),

    ]



    for instr in instructions2:

        dag2.add_instruction(instr)



    dag2.add_dep(0, 2)

    dag2.add_dep(1, 2)



    schedule2 = dag2.list_schedule(issue_width=1)  # 限制每周期只能发1条

    analyzer.print_schedule(schedule2, dag2.instructions)

