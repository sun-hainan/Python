# -*- coding: utf-8 -*-
"""
算法实现：编译器内核 / register_alloc_graph

本文件实现 register_alloc_graph 相关的算法功能。
"""

from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict, deque
import random

from liveness_analysis import LivenessAnalysis, build_interference_graph


class RegisterAllocator:
    """
    图着色寄存器分配器

    算法: Chaitin-Briggs
    1. 构建干涉图
    2. 简化阶段: 移除度数<颜色的节点
    3. 溢出检测: 选择溢出候选
    4. 着色阶段: 重新选择颜色
    5. 溢出处理: 将溢出变量放到内存
    """

    def __init__(self, live_analysis: LivenessAnalysis,
                 num_registers: int = 16):
        self.live_analysis = live_analysis
        self.num_registers = num_registers
        self.interference_graph: Dict[str, Set[str]] = {}
        self.degree: Dict[str, int] = {}  # 节点度数
        self.color: Dict[str, int] = {}  # 颜色分配结果
        self.spill_candidates: Set[str] = set()  # 溢出候选
        self.stack: List[str] = []  # 简化栈
        self.registers: List[str] = [f"r{i}" for i in range(num_registers)]  # 寄存器名

    def allocate(self) -> Dict[str, int]:
        """
        执行寄存器分配

        返回:
            变量 -> 寄存器编号 的映射
        """
        # 构建干涉图
        self.interference_graph = build_interference_graph(self.live_analysis)

        # 初始化度数
        for var in self.interference_graph:
            self.degree[var] = len(self.interference_graph[var])

        # 简化阶段
        self._simplify()

        # 着色阶段
        self._select()

        return self.color

    def _simplify(self):
        """
        简化阶段
        将度数<颜色数的节点压入栈,直到图为空或所有节点度数>=K
        """
        self.stack.clear()
        available = set(self.interference_graph.keys())

        while available:
            # 找到度数< K的节点
            low_degree_nodes = [v for v in available if self.degree[v] < self.num_registers]

            if not low_degree_nodes:
                # 所有节点度数都>=K,选择溢出候选
                if available:
                    spill = self._choose_spill_candidate(available)
                    self.spill_candidates.add(spill)
                    available.remove(spill)
                    self._update_degrees(spill, available)
                break

            # 选择一个低度数节点
            node = random.choice(low_degree_nodes)
            self.stack.append(node)
            available.remove(node)

            # 更新相关节点的度数
            self._update_degrees(node, available)

    def _update_degrees(self, node: str, available: Set[str]):
        """更新邻居节点的度数"""
        neighbors = self.interference_graph.get(node, set())
        for neighbor in neighbors:
            if neighbor in available:
                self.degree[neighbor] -= 1

    def _choose_spill_candidate(self, candidates: Set[str]) -> str:
        """
        选择溢出候选
        启发式: 选择具有最高溢出代价的节点
        """
        # 简化:随机选择
        # 实际实现应考虑:use/def频率,循环深度等
        return random.choice(list(candidates))

    def _select(self):
        """
        着色阶段
        从栈中弹出节点,选择与邻居不同的颜色
        """
        self.color.clear()

        while self.stack:
            node = self.stack.pop()

            # 找出邻居使用的颜色
            used_colors = set()
            neighbors = self.interference_graph.get(node, set())
            for neighbor in neighbors:
                if neighbor in self.color:
                    used_colors.add(self.color[neighbor])

            # 选择第一个未使用的颜色
            for c in range(self.num_registers):
                if c not in used_colors:
                    self.color[node] = c
                    break
            else:
                # 没有可用颜色,需要溢出
                self.spill_candidates.add(node)
                self.color[node] = -1  # 标记为溢出

    def get_register(self, var: str) -> str:
        """获取变量分配的寄存器名"""
        if var in self.color:
            reg_num = self.color[var]
            if reg_num >= 0:
                return self.registers[reg_num]
        return f"mem[{var}]"  # 溢出到内存

    def is_spilled(self, var: str) -> bool:
        """检查变量是否溢出"""
        return var in self.spill_candidates

    def get_spill_cost(self, var: str) -> float:
        """
        计算溢出代价
        简化实现: 基于变量的活跃区间长度和使用频率
        """
        cost = 0.0
        for interval in self.live_analysis.intervals:
            if interval.variable == var:
                # 代价 = 区间长度 * 访问频率
                length = interval.end - interval.start
                cost = length * 1.0
                break
        return cost


class GraphColoring:
    """
    图着色算法(通用版)
    """

    def __init__(self, num_colors: int):
        self.num_colors = num_colors
        self.graph: Dict[str, Set[str]] = {}
        self.degree: Dict[str, int] = {}
        self.colors: Dict[str, int] = {}
        self.stack: List[str] = []

    def add_edge(self, u: str, v: str):
        """添加无向边"""
        if u not in self.graph:
            self.graph[u] = set()
        if v not in self.graph:
            self.graph[v] = set()
        self.graph[u].add(v)
        self.graph[v].add(u)

    def colorize(self) -> bool:
        """
        执行图着色

        返回:
            True表示着色成功, False表示需要简化
        """
        self._init_degrees()

        while self.graph:
            # 找低度数节点
            low_degree = [v for v in self.graph if len(self.graph[v]) < self.num_colors]

            if low_degree:
                # 选择并移除
                v = self._select_node(low_degree)
                self.stack.append(v)
                self._remove_node(v)
            else:
                # 需要简化,选择溢出
                return False

        # 为所有节点着色
        self._assign_colors()
        return True

    def _init_degrees(self):
        """初始化度数"""
        for node in self.graph:
            self.degree[node] = len(self.graph[node])

    def _select_node(self, candidates: List[str]) -> str:
        """选择节点"""
        return candidates[0]

    def _remove_node(self, v: str):
        """移除节点"""
        neighbors = list(self.graph[v])
        for u in neighbors:
            self.graph[u].discard(v)
        del self.graph[v]

    def _assign_colors(self):
        """为栈中节点分配颜色"""
        self.colors.clear()

        while self.stack:
            v = self.stack.pop()

            # 重建图,添加v和邻居
            used = set()
            for u in self.graph:
                if v in self.graph[u]:
                    if u in self.colors:
                        used.add(self.colors[u])

            # 选择颜色
            for c in range(self.num_colors):
                if c not in used:
                    self.colors[v] = c
                    break
            else:
                self.colors[v] = -1

            # 临时添加v回图中(用于着色后续节点)
            self.graph[v] = set()


def print_allocation(allocator: RegisterAllocator):
    """打印分配结果"""
    print("=== 寄存器分配结果 ===")
    print(f"寄存器数量: {allocator.num_registers}")
    print(f"干涉图节点数: {len(allocator.interference_graph)}")

    print("\n分配结果:")
    for var, reg_num in sorted(allocator.color.items()):
        if reg_num >= 0:
            print(f"  {var} -> r{reg_num}")
        else:
            print(f"  {var} -> [溢出到内存]")

    if allocator.spill_candidates:
        print(f"\n溢出变量: {sorted(allocator.spill_candidates)}")


if __name__ == "__main__":
    from intermediate_representation import IRGenerator, Address, OpCode
    from basic_block import BasicBlockBuilder
    from cfg_builder import ControlFlowGraph
    from liveness_analysis import LivenessAnalysis

    # 生成测试IR
    gen = IRGenerator()

    # 示例: 多寄存器使用
    gen.emit(OpCode.LOAD, result=Address.temp("a"), arg1=Address.variable("a"))
    gen.emit(OpCode.LOAD, result=Address.temp("b"), arg1=Address.variable("b"))
    t1 = gen.new_temp()
    gen.emit_binary(OpCode.ADD, t1, Address.temp("a"), Address.temp("b"))
    t2 = gen.new_temp()
    gen.emit_binary(OpCode.MUL, t2, t1, Address.variable("c"))
    t3 = gen.new_temp()
    gen.emit_binary(OpCode.SUB, t3, t2, Address.variable("d"))
    gen.emit(OpCode.STORE, result=Address.variable("x"), arg1=t3)

    instructions = gen.generate()

    # 构建CFG和活跃性分析
    builder = BasicBlockBuilder()
    blocks = builder.build(instructions)
    cfg = ControlFlowGraph(blocks)
    live = LivenessAnalysis(instructions, cfg)
    live.analyze()

    print("=== 干涉图 ===")
    ig = build_interference_graph(live)
    for var, neighbors in sorted(ig.items()):
        print(f"  {var}: {sorted(neighbors)}")

    # 寄存器分配
    print("\n=== 寄存器分配 (8个寄存器) ===")
    allocator = RegisterAllocator(live, num_registers=8)
    result = allocator.allocate()
    print_allocation(allocator)

    # 测试图着色算法
    print("\n=== 图着色测试 ===")
    gc = GraphColoring(num_colors=4)
    gc.add_edge("A", "B")
    gc.add_edge("A", "C")
    gc.add_edge("A", "D")
    gc.add_edge("B", "C")
    gc.add_edge("C", "D")

    success = gc.colorize()
    print(f"着色成功: {success}")
    print(f"颜色分配: {gc.colors}")
