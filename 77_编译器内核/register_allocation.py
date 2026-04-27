# -*- coding: utf-8 -*-

"""

算法实现：编译器内核 / register_allocation



本文件实现 register_allocation 相关的算法功能。

"""



from typing import Dict, List, Set, Tuple, Optional, Any

from dataclasses import dataclass, field

from enum import Enum



# ========== 活跃性分析 ==========



@dataclass

class LiveInterval:

    """活跃区间"""

    variable: str

    start: int          # 开始点（指令序号）

    end: int           # 结束点

    reg: Optional[str] = None  # 分配的寄存器

    

    def __repr__(self):

        return f"{self.variable}: [{self.start}, {self.end}] -> {self.reg}"





class LivenessAnalyzer:

    """

    活跃性分析

    计算每个变量的活跃区间

    """

    

    def __init__(self, instructions: List):

        self.instructions = instructions

        self.live_ranges: Dict[str, List[Tuple[int, int]]] = {}  # variable -> [(start, end), ...]

    

    def analyze(self) -> List[LiveInterval]:

        """

        执行活跃性分析

        返回: 活跃区间列表

        """

        # 构建活跃性信息

        live_at = [set() for _ in range(len(self.instructions))]

        

        # 反向扫描，计算每个点的活跃变量

        for i in reversed(range(len(self.instructions))):

            instr = self.instructions[i]

            

            # 当前点的活跃变量

            if i + 1 < len(live_at):

                live_at[i] = live_at[i + 1].copy()

            else:

                live_at[i] = set()

            

            # 变量被使用（在定义之前还是之后？）

            for arg in getattr(instr, 'args', []):

                if arg:

                    live_at[i].add(arg)

            

            # 定义清除

            if hasattr(instr, 'result') and instr.result:

                live_at[i].discard(instr.result)

                # 定义后变量变为活跃

                live_at[i].add(instr.result)

        

        # 构建活跃区间

        intervals = []

        

        # 收集所有变量

        all_vars = set()

        for instr in self.instructions:

            if hasattr(instr, 'result') and instr.result:

                all_vars.add(instr.result)

            for arg in getattr(instr, 'args', []):

                if arg:

                    all_vars.add(arg)

        

        for var in all_vars:

            # 找活跃区间

            in_range = False

            start = 0

            end = 0

            

            for i, live_set in enumerate(live_at):

                if var in live_set:

                    if not in_range:

                        start = i

                        in_range = True

                    end = i

            

            if in_range:

                intervals.append(LiveInterval(variable=var, start=start, end=end))

        

        return intervals

    

    def build_interference_graph(self, intervals: List[LiveInterval]) -> Dict[str, Set[str]]:

        """

        构建干扰图

        两个变量干扰：它们的活跃区间有交集

        """

        graph: Dict[str, Set[str]] = {}

        

        for i, interval1 in enumerate(intervals):

            graph[interval1.variable] = set()

            

            for j, interval2 in enumerate(intervals):

                if i != j:

                    # 检查活跃区间是否重叠

                    if not (interval1.end < interval2.start or interval2.end < interval1.start):

                        graph[interval1.variable].add(interval2.variable)

        

        return graph





# ========== 图着色寄存器分配 ==========



class InterferenceGraph:

    """干扰图"""

    

    def __init__(self):

        self.nodes: Set[str] = set()

        self.edges: Dict[str, Set[str]] = {}

    

    def add_node(self, node: str):

        if node not in self.edges:

            self.edges[node] = set()

            self.nodes.add(node)

    

    def add_edge(self, u: str, v: str):

        if u not in self.edges:

            self.edges[u] = set()

        if v not in self.edges:

            self.edges[v] = set()

        self.edges[u].add(v)

        self.edges[v].add(u)

    

    def get_neighbors(self, node: str) -> Set[str]:

        return self.edges.get(node, set()).copy()

    

    def remove_node(self, node: str):

        if node in self.edges:

            for neighbor in self.edges[node]:

                self.edges[neighbor].discard(node)

            del self.edges[node]

            self.nodes.discard(node)





class ChaitinAllocator:

    """

    Chaitin-Briggs图着色寄存器分配

    启发式算法，简化实现

    """

    

    def __init__(self, max_colors: int = 16):

        self.max_colors = max_colors

        self.available_regs = [f"r{i}" for i in range(max_colors)]

        self.color_map: Dict[str, str] = {}  # variable -> register

        self.stack: List[str] = []

    

    def allocate(self, graph: InterferenceGraph) -> Dict[str, str]:

        """

        执行寄存器分配

        返回: variable -> register 映射

        """

        self.color_map = {}

        self.stack = []

        

        # 简化：按度数排序，移除低度数节点

        working_graph = InterferenceGraph()

        working_graph.nodes = graph.nodes.copy()

        working_graph.edges = {k: v.copy() for k, v in graph.edges.items()}

        

        # 移除所有可能溢出（度数 >= max_colors）的节点

        # 实际应该迭代处理

        to_remove = []

        

        for node in list(working_graph.nodes):

            if len(working_graph.get_neighbors(node)) < self.max_colors:

                to_remove.append(node)

        

        for node in to_remove:

            working_graph.remove_node(node)

            self.stack.append(node)

        

        # 分配颜色

        while self.stack:

            node = self.stack.pop()

            

            # 找出已分配颜色的邻居

            used_colors = set()

            for neighbor in working_graph.edges.get(node, []):

                if neighbor in self.color_map:

                    used_colors.add(self.color_map[neighbor])

            

            # 选择第一个可用颜色

            for reg in self.available_regs:

                if reg not in used_colors:

                    self.color_map[node] = reg

                    break

        

        return self.color_map





class BriggsAllocator:

    """

    Briggs图着色算法

    改进版，使用更少的溢出

    """

    

    def __init__(self, max_colors: int = 16):

        self.max_colors = max_colors

        self.available_regs = [f"r{i}" for i in range(max_colors)]

        self.color_map: Dict[str, str] = {}

        self.adj_list: Dict[str, Set[str]] = {}

        self.simplify_worklist: List[str] = []

        self.freeze_worklist: List[str] = []

        self.spill_worklist: List[str] = []

    

    def build_graph(self, intervals: List[LiveInterval]) -> InterferenceGraph:

        """从活跃区间构建干扰图"""

        graph = InterferenceGraph()

        

        for interval in intervals:

            graph.add_node(interval.variable)

        

        # 检查区间重叠

        for i in range(len(intervals)):

            for j in range(i + 1, len(intervals)):

                if not (intervals[i].end < intervals[j].start or 

                        intervals[j].end < intervals[i].start):

                    graph.add_edge(intervals[i].variable, intervals[j].variable)

        

        return graph

    

    def allocate(self, graph: InterferenceGraph) -> Dict[str, str]:

        """执行Briggs算法"""

        self.color_map = {}

        self.adj_list = {n: graph.get_neighbors(n) for n in graph.nodes}

        

        # 初始分类

        simplify_set = set()

        

        for node in graph.nodes:

            if len(self.adj_list[node]) < self.max_colors:

                simplify_set.add(node)

        

        # 简化阶段

        while simplify_set:

            node = simplify_set.pop()

            

            # 选择度数 < K 的节点

            neighbors = self.adj_list[node].copy()

            

            for neighbor in neighbors:

                self.adj_list[neighbor].discard(node)

                self.adj_list[node].discard(neighbor)

                

                if len(self.adj_list[neighbor]) < self.max_colors and neighbor not in simplify_set:

                    simplify_set.add(neighbor)

            

            self.color_map[node] = None  # 暂定，稍后着色

        

        # 选择阶段

        for node in self.color_map:

            if self.color_map[node] is None:

                # 找可用颜色

                used = set()

                for neighbor in self.adj_list.get(node, []):

                    if neighbor in self.color_map and self.color_map[neighbor]:

                        used.add(self.color_map[neighbor])

                

                for reg in self.available_regs:

                    if reg not in used:

                        self.color_map[node] = reg

                        break

        

        return self.color_map





# ========== 线性扫描寄存器分配 ==========



class LinearScanAllocator:

    """

    线性扫描寄存器分配

    高效的寄存器分配算法

    """

    

    def __init__(self, max_regs: int = 16):

        self.max_regs = max_regs

        self.allocations: Dict[str, str] = {}  # variable -> register

        self.active: List[LiveInterval] = []   # 当前活跃区间

    

    def allocate(self, intervals: List[LiveInterval]) -> Dict[str, str]:

        """

        执行线性扫描分配

        """

        # 按起始点排序

        sorted_intervals = sorted(intervals, key=lambda x: x.start)

        

        self.active = []

        self.allocations = {}

        

        for interval in sorted_intervals:

            # 过期处理：移除已结束的区间

            self.active = [a for a in self.active if a.end >= interval.start]

            

            # 检查是否已有分配

            if interval.variable in self.allocations:

                continue

            

            # 尝试分配

            if len(self.active) < self.max_regs:

                # 有空闲寄存器

                reg = f"r{len(self.active)}"

                self.allocations[interval.variable] = reg

                interval.reg = reg

                self.active.append(interval)

            else:

                # 需要溢出（spill）

                # 找到结束最晚的区间溢出

                spill_idx = self._find_spill_candidate(interval)

                if spill_idx >= 0:

                    spilled = self.active[spill_idx]

                    self.allocations[spilled.variable] = f"r{spill_idx}"

                    spilled.reg = f"r{spill_idx}"

                    self.allocations[interval.variable] = f"r{spill_idx}"

                    interval.reg = f"r{spill_idx}"

                    self.active[spill_idx] = interval

                else:

                    # 所有活跃区间都需要溢出到内存

                    self.allocations[interval.variable] = "spill"

        

        return self.allocations

    

    def _find_spill_candidate(self, new_interval: LiveInterval) -> int:

        """

        找到可以溢出的区间

        返回: 溢出区间的索引，或-1表示全部溢出

        """

        # 选择结束最晚的区间（因为它的活跃范围最接近new_interval的起点）

        max_end_idx = -1

        max_end = -1

        

        for i, interval in enumerate(self.active):

            if interval.end > max_end:

                max_end = interval.end

                max_end_idx = i

        

        return max_end_idx





# ========== 寄存器重命名 ==========



class RegisterRenamer:

    """

    寄存器重命名器

    处理SSA形式中的寄存器分配

    """

    

    def __init__(self):

        self.reg_map: Dict[str, str] = {}  # SSA var -> physical reg

    

    def rename(self, ssa_var: str, physical_reg: str):

        """将SSA变量映射到物理寄存器"""

        self.reg_map[ssa_var] = physical_reg

    

    def get_reg(self, ssa_var: str) -> Optional[str]:

        """获取SSA变量对应的物理寄存器"""

        return self.reg_map.get(ssa_var)





if __name__ == "__main__":

    print("=" * 60)

    print("寄存器分配演示")

    print("=" * 60)

    

    # 模拟指令

    class Instr:

        def __init__(self, opcode, result=None, args=None):

            self.opcode = opcode

            self.result = result

            self.args = args if args else []

    

    instructions = [

        Instr("add", "t0", ["a", "b"]),

        Instr("sub", "t1", ["t0", "c"]),

        Instr("mul", "t0", ["t1", "d"]),  # t0被重新定义

        Instr("add", "t2", ["t0", "e"]),

    ]

    

    # 1. 活跃性分析

    print("\n--- 活跃性分析 ---")

    analyzer = LivenessAnalyzer(instructions)

    intervals = analyzer.analyze()

    

    for interval in intervals:

        print(f"  {interval}")

    

    # 构建干扰图

    print("\n--- 干扰图 ---")

    graph = analyzer.build_interference_graph(intervals)

    

    for node, neighbors in graph.items():

        print(f"  {node} -- {neighbors}")

    

    # 2. Chaitin分配

    print("\n--- Chaitin图着色分配 ---")

    ig = InterferenceGraph()

    

    for node, neighbors in graph.items():

        ig.add_node(node)

        for neighbor in neighbors:

            ig.add_edge(node, neighbor)

    

    chaitin = ChaitinAllocator(max_colors=3)

    chaitin_result = chaitin.allocate(ig)

    

    print(f"  分配结果: {chaitin_result}")

    print(f"  寄存器数: {len(set(chaitin_result.values()))}")

    

    # 3. 线性扫描

    print("\n--- 线性扫描分配 ---")

    linear = LinearScanAllocator(max_regs=3)

    linear_result = linear.allocate(intervals)

    

    print(f"  分配结果: {linear_result}")

    

    print("\n寄存器分配算法对比:")

    print("  Chaitin/Briggs: 经典图着色，性能好，但复杂")

    print("  线性扫描: O(n log n)，适合简单场景")

    print("  目标: 最小化溢出，最小化寄存器间的移动")

