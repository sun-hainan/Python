# -*- coding: utf-8 -*-

"""

算法实现：编译器优化 / register_allocation



本文件实现 register_allocation 相关的算法功能。

"""



from typing import List, Set, Dict, Optional, Tuple

from collections import defaultdict





class InterferenceGraph:

    """

    干扰图

    顶点 = 虚拟寄存器

    边 = 两个寄存器同时活跃(不能分配同一物理寄存器)

    """

    

    def __init__(self):

        self.graph: Dict[str, Set[str]] = defaultdict(set)

        self.variables: Set[str] = set()

    

    def add_vertex(self, var: str):

        """添加顶点"""

        self.variables.add(var)

        if var not in self.graph:

            self.graph[var] = set()

    

    def add_edge(self, v1: str, v2: str):

        """添加边(干扰)"""

        if v1 != v2:

            self.graph[v1].add(v2)

            self.graph[v2].add(v1)

    

    def neighbors(self, var: str) -> Set[str]:

        """获取邻居"""

        return self.graph.get(var, set())

    

    def degree(self, var: str) -> int:

        """获取度数"""

        return len(self.graph.get(var, set()))

    

    def remove_vertex(self, var: str):

        """移除顶点"""

        if var in self.graph:

            for neighbor in self.graph[var]:

                self.graph[neighbor].discard(var)

            del self.graph[var]

        self.variables.discard(var)

    

    def copy(self):

        """复制图"""

        new_graph = InterferenceGraph()

        new_graph.graph = {k: v.copy() for k, v in self.graph.items()}

        new_graph.variables = self.variables.copy()

        return new_graph





class RegisterAllocator:

    """

    图着色寄存器分配器

    使用Chaitin-Briggs算法

    """

    

    def __init__(self, num_registers: int):

        """

        初始化

        

        Args:

            num_registers: 可用物理寄存器数量

        """

        self.k = num_registers

        self.ig = InterferenceGraph()

        self.allocations: Dict[str, int] = {}  # 虚拟寄存器 -> 物理寄存器

        self.spill_candidates: List[str] = []

    

    def build_interference_graph(self, live_intervals: Dict[str, List[Tuple[int, int]]]):

        """

        从活跃区间构建干扰图

        

        Args:

            live_intervals: {var: [(start, end), ...]}

        """

        # 收集所有变量

        all_vars = set(live_intervals.keys())

        for var in all_vars:

            self.ig.add_vertex(var)

        

        # 检查每对变量是否活跃重叠

        vars_list = list(all_vars)

        for i, v1 in enumerate(vars_list):

            for v2 in vars_list[i + 1:]:

                if self._intervals_overlap(live_intervals[v1], live_intervals[v2]):

                    self.ig.add_edge(v1, v2)

    

    def _intervals_overlap(self, intervals1: List[Tuple[int, int]], 

                          intervals2: List[Tuple[int, int]]) -> bool:

        """检查两个区间列表是否重叠"""

        for s1, e1 in intervals1:

            for s2, e2 in intervals2:

                if s1 <= e2 and s2 <= e1:  # 重叠条件

                    return True

        return False

    

    def color_graph(self) -> Tuple[bool, Dict[str, int]]:

        """

        图着色

        

        Returns:

            (是否成功, {var: register})

        """

        # 创建工作副本

        ig = self.ig.copy()

        

        # 栈用于回溯

        stack = []

        

        # 简化:使用贪心着色

        while ig.variables:

            # 找度数小于k的顶点

            low_degree = [v for v in ig.variables if ig.degree(v) < self.k]

            

            if low_degree:

                # 选择度数最小的

                v = min(low_degree, key=lambda x: ig.degree(x))

                stack.append(v)

                ig.remove_vertex(v)

            else:

                # 所有顶点度数都>=k,需要溢出

                # 选择度数最大的作为溢出候选

                v = max(ig.variables, key=lambda x: ig.degree(x))

                stack.append(v)

                ig.remove_vertex(v)

                self.spill_candidates.append(v)

        

        # 着色

        allocations = {}

        available = set(range(self.k))

        

        while stack:

            v = stack.pop()

            

            # 恢复邻居的可用寄存器

            neighbors_used = set(allocations.get(n, -1) for n in self.ig.neighbors(v) if n in allocations)

            available = set(range(self.k)) - neighbors_used

            

            if available:

                allocations[v] = available.pop()

                # 恢复顶点到ig以便后续处理

                self.ig.add_vertex(v)

            else:

                # 无法分配

                return False, {}

        

        self.allocations = allocations

        return True, allocations

    

    def allocate(self, live_intervals: Dict[str, List[Tuple[int, int]]]) -> Tuple[bool, Dict[str, int]]:

        """

        执行寄存器分配

        

        Args:

            live_intervals: 活跃区间

        

        Returns:

            (是否成功, 分配结果)

        """

        self.spill_candidates = []

        self.build_interference_graph(live_intervals)

        return self.color_graph()





def build_live_intervals(instructions: List[Dict]) -> Dict[str, List[Tuple[int, int]]]:

    """

    从指令序列构建活跃区间

    

    Args:

        instructions: [{'def': str, 'uses': [str], 'id': int}, ...]

    

    Returns:

        {var: [(start, end), ...]}

    """

    intervals = defaultdict(list)

    

    # 跟踪每个变量的定义和使用位置

    last_use = {}  # {var: last_use_position}

    

    for i, instr in enumerate(instructions):

        # 更新最后使用

        for var in instr.get('uses', []):

            last_use[var] = i

    

    # 再次遍历构建区间

    for i, instr in enumerate(instructions):

        var = instr.get('def')

        if var:

            # 找到这个定义的最后使用

            end = last_use.get(var, i)

            intervals[var].append((i, end))

    

    return dict(intervals)





def simple_register_allocate(num_regs: int, 

                             instructions: List[Dict]) -> Tuple[bool, Dict[str, int], List[str]]:

    """

    简单寄存器分配

    

    Args:

        num_regs: 物理寄存器数量

        instructions: 指令列表

    

    Returns:

        (成功, 分配, 溢出变量)

    """

    # 构建活跃区间

    live_intervals = build_live_intervals(instructions)

    

    # 分配

    allocator = RegisterAllocator(num_regs)

    success, alloc = allocator.allocate(live_intervals)

    

    return success, alloc, allocator.spill_candidates





# 测试代码

if __name__ == "__main__":

    # 测试1: 简单例子

    print("测试1 - 简单寄存器分配:")

    

    instructions = [

        {'id': 0, 'def': 'a', 'uses': ['x', 'y']},

        {'id': 1, 'def': 'b', 'uses': ['a']},

        {'id': 2, 'def': 'c', 'uses': ['a', 'b']},

        {'id': 3, 'def': 'd', 'uses': ['c']},

    ]

    

    success, alloc, spill = simple_register_allocate(3, instructions)

    

    print(f"  指令: {instructions}")

    print(f"  分配成功: {success}")

    print(f"  分配: {alloc}")

    print(f"  溢出: {spill}")

    

    # 测试2: 复杂例子

    print("\n测试2 - 复杂寄存器分配:")

    

    # 活跃区间:

    # a: [0, 3]

    # b: [1, 2]

    # c: [1, 4]

    # d: [2, 5]

    # e: [3, 6]

    

    live_intervals = {

        'a': [(0, 3)],

        'b': [(1, 2)],

        'c': [(1, 4)],

        'd': [(2, 5)],

        'e': [(3, 6)],

    }

    

    allocator = RegisterAllocator(num_registers=3)

    success, alloc = allocator.allocate(live_intervals)

    

    print(f"  活跃区间: {live_intervals}")

    print(f"  分配成功: {success}")

    print(f"  分配: {alloc}")

    print(f"  溢出候选: {allocator.spill_candidates}")

    

    # 验证干扰

    print("\n  验证干扰图:")

    ig = allocator.ig

    for var in ig.variables:

        print(f"    {var}: 邻居={ig.neighbors(var)}, 度数={ig.degree(var)}")

    

    # 测试3: 需要溢出

    print("\n测试3 - 需要溢出:")

    

    # 5个变量,只有2个寄存器

    live_intervals2 = {

        'a': [(0, 10)],

        'b': [(0, 10)],

        'c': [(0, 10)],

        'd': [(0, 10)],

        'e': [(0, 10)],

    }

    

    allocator2 = RegisterAllocator(num_registers=2)

    success2, alloc2 = allocator2.allocate(live_intervals2)

    

    print(f"  分配成功: {success2}")

    print(f"  分配: {alloc2}")

    print(f"  溢出: {allocator2.spill_candidates}")

    

    # 测试4: 验证分配正确性

    print("\n测试4 - 分配验证:")

    

    success, alloc, spill = simple_register_allocate(3, instructions)

    

    if success:

        # 检查是否有干扰的变量分配了同一寄存器

        for var1 in alloc:

            for var2 in alloc:

                if var1 != var2:

                    # 检查是否干扰

                    if allocator.ig.neighbors(var1).__contains__(var2):

                        if alloc[var1] == alloc[var2]:

                            print(f"  错误: {var1}和{var2}干扰但分配了同一寄存器{alloc[var1]}")

                        else:

                            pass  # 正确

    

    # 测试5: 实际代码示例

    print("\n测试5 - 实际代码示例:")

    

    code_instrs = [

        {'id': 0, 'def': 't1', 'uses': ['a', 'b']},  # t1 = a + b

        {'id': 1, 'def': 't2', 'uses': ['t1', 'c']},  # t2 = t1 + c

        {'id': 2, 'def': 'd', 'uses': ['t2']},        # d = t2

        {'id': 3, 'def': 't3', 'uses': ['e', 'f']},  # t3 = e + f

        {'id': 4, 'def': 'g', 'uses': ['t3']},        # g = t3

    ]

    

    success, alloc, spill = simple_register_allocate(4, code_instrs)

    

    print(f"  代码:")

    for instr in code_instrs:

        print(f"    {instr['id']}: {instr.get('def', '?')} = {instr.get('uses', [])}")

    

    print(f"  分配: {alloc}")

    print(f"  成功: {success}, 溢出: {spill}")

    

    print("\n所有测试完成!")

