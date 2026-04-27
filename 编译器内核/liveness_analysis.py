# -*- coding: utf-8 -*-
"""
算法实现：编译器内核 / liveness_analysis

本文件实现 liveness_analysis 相关的算法功能。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict, deque

from intermediate_representation import TACInstruction, OpCode, Address
from basic_block import BasicBlock
from cfg_builder import ControlFlowGraph


@dataclass
class LiveInterval:
    """活跃区间"""
    variable: str  # 变量名
    start: int  # 区间开始(指令索引)
    end: int  # 区间结束(指令索引)


class LivenessAnalysis:
    """
    活跃性分析

    使用数据流分析计算变量的活跃区间
    算法: 反向数据流,迭代求解
    """

    def __init__(self, instructions: List[TACInstruction], cfg: ControlFlowGraph):
        self.instructions: List[TACInstruction] = instructions  # 指令列表
        self.cfg: ControlFlowGraph = cfg  # 控制流图
        self.live_in: Dict[int, Set[str]] = {}  # 每条指令入口时的活跃变量
        self.live_out: Dict[int, Set[str]] = {}  # 每条指令出口时的活跃变量
        self.use: Dict[int, Set[str]] = {}  # 每条指令的use集合
        self.def_: Dict[int, Set[str]] = {}  # 每条指令的def集合
        self.variables: Set[str] = set()  # 所有变量
        self.intervals: List[LiveInterval] = []  # 活跃区间

    def analyze(self) -> Dict[int, Set[str]]:
        """
        执行活跃性分析

        返回:
            live_in字典: 指令索引 -> 活跃变量集合
        """
        # 初始化
        self._initialize()

        # 迭代计算
        changed = True
        iterations = 0
        while changed and iterations < 100:
            changed = False
            iterations += 1

            # 逆序遍历(从后往前)
            for i in reversed(range(len(self.instructions))):
                old_live_out = self.live_out.get(i, set()).copy()

                # live_out[i] = union of live_in of successors
                instr = self.instructions[i]
                succ_indices = self._get_successors(i)

                new_live_out = set()
                for succ in succ_indices:
                    if succ in self.live_in:
                        new_live_out |= self.live_in[succ]

                self.live_out[i] = new_live_out

                # live_in[i] = use[i] union (live_out[i] - def[i])
                self.live_in[i] = self.use.get(i, set()) | (
                    self.live_out.get(i, set()) - self.def_.get(i, set())
                )

                if self.live_in[i] != old_live_out:
                    changed = True

        # 计算活跃区间
        self._compute_intervals()

        return self.live_in

    def _initialize(self):
        """初始化数据结构"""
        self.live_in = {i: set() for i in range(len(self.instructions))}
        self.live_out = {i: set() for i in range(len(self.instructions))}
        self.use = {i: set() for i in range(len(self.instructions))}
        self.def_ = {i: set() for i in range(len(self.instructions))}

        # 分析每条指令的use和def
        for i, instr in enumerate(self.instructions):
            use_set = set()
            def_set = set()

            # 提取操作数
            if instr.arg1:
                var = self._get_variable_name(instr.arg1)
                if var:
                    use_set.add(var)
                    self.variables.add(var)

            if instr.arg2:
                var = self._get_variable_name(instr.arg2)
                if var:
                    use_set.add(var)
                    self.variables.add(var)

            # 结果变量
            if instr.result:
                var = self._get_variable_name(instr.result)
                if var and instr.op not in [OpCode.LABEL, OpCode.FUNC_BEGIN, OpCode.FUNC_END]:
                    def_set.add(var)
                    self.variables.add(var)

            self.use[i] = use_set
            self.def_[i] = def_set

    def _get_variable_name(self, addr: Address) -> Optional[str]:
        """从地址获取变量名"""
        if addr.kind in ["var", "temp"]:
            return str(addr.value)
        return None

    def _get_successors(self, index: int) -> List[int]:
        """获取指令的后继指令索引"""
        instr = self.instructions[index]
        succs = []

        # 跳转到标签
        if instr.op in [OpCode.JUMP, OpCode.JUMP_IF, OpCode.JUMP_IF_NOT]:
            if instr.result and instr.result.kind == "label":
                target_label = instr.result.value
                target_idx = self._find_label_index(target_label)
                if target_idx is not None:
                    succs.append(target_idx)

        # 普通顺序后继
        if instr.op not in [OpCode.JUMP, OpCode.JUMP_IF, OpCode.JUMP_IF_NOT,
                           OpCode.RETURN, OpCode.FUNC_END]:
            if index + 1 < len(self.instructions):
                succs.append(index + 1)

        return succs

    def _find_label_index(self, label: str) -> Optional[int]:
        """查找标签对应的指令索引"""
        for i, instr in enumerate(self.instructions):
            if instr.op == OpCode.LABEL and instr.result and instr.result.value == label:
                return i
        return None

    def _compute_intervals(self):
        """计算活跃区间"""
        # 变量 -> 首次出现, 最后出现
        var_first: Dict[str, int] = {}
        var_last: Dict[str, int] = {}

        for i, instr in enumerate(self.instructions):
            # use
            for var in self.use.get(i, set()):
                if var not in var_first:
                    var_first[var] = i
                var_last[var] = i

            # def
            for var in self.def_.get(i, set()):
                if var not in var_first:
                    var_first[var] = i
                var_last[var] = i

        # 构建活跃区间
        self.intervals = []
        for var in self.variables:
            if var in var_first:
                # 修正: def之后才能使用,检查是否有use
                start = var_first[var]
                end = var_last.get(var, start)

                # 如果变量被定义但从未使用,不创建区间
                # 简化处理
                self.intervals.append(LiveInterval(variable=var, start=start, end=end))

    def get_live_at(self, index: int) -> Set[str]:
        """获取指定指令处的活跃变量"""
        return self.live_in.get(index, set())

    def get_live_out_at(self, index: int) -> Set[str]:
        """获取指定指令出口处的活跃变量"""
        return self.live_out.get(index, set())

    def is_live_after(self, index: int, var: str) -> bool:
        """检查变量在指令之后是否活跃"""
        return var in self.live_out.get(index, set())

    def is_live_before(self, index: int, var: str) -> bool:
        """检查变量在指令之前是否活跃"""
        return var in self.live_in.get(index, set())


def build_interference_graph(live_analysis: LivenessAnalysis) -> Dict[str, Set[str]]:
    """
    构建干涉图
    用于寄存器分配

    规则:
    1. 如果两个变量在同一点都活跃,则它们相互干涉
    2. 源寄存器和目标寄存器相同时不干涉
    """
    n = len(live_analysis.instructions)
    interference: Dict[str, Set[str]] = defaultdict(set)

    # 初始化
    for var in live_analysis.variables:
        interference[var] = set()

    # 遍历每条指令
    for i in range(n):
        live_out = live_analysis.get_live_out_at(i)
        instr = live_analysis.instructions[i]

        # 获取def变量
        def_vars = live_analysis.def_.get(i, set())

        # 所有活跃变量相互干涉(def变量除外自己)
        for v1 in def_vars:
            for v2 in live_out:
                if v1 != v2:
                    interference[v1].add(v2)
                    interference[v2].add(v1)

    return dict(interference)


def print_liveness(analysis: LivenessAnalysis):
    """打印活跃性分析结果"""
    print("=== 活跃性分析结果 ===")
    print(f"\n{'Index':<6} {'Instruction':<40} {'USE':<15} {'DEF':<15} {'LIVE_IN':<20} {'LIVE_OUT'}")
    print("-" * 120)

    for i, instr in enumerate(analysis.instructions):
        use_str = ",".join(sorted(analysis.use.get(i, set())))
        def_str = ",".join(sorted(analysis.def_.get(i, set())))
        live_in_str = ",".join(sorted(analysis.live_in.get(i, set())))
        live_out_str = ",".join(sorted(analysis.live_out.get(i, set())))

        instr_str = str(instr)[:38]
        print(f"{i:<6} {instr_str:<40} {use_str:<15} {def_str:<15} {live_in_str:<20} {live_out_str}")

    print(f"\n活跃区间:")
    for interval in analysis.intervals:
        print(f"  {interval.variable}: [{interval.start}, {interval.end}]")


if __name__ == "__main__":
    from intermediate_representation import IRGenerator, Address
    from basic_block import BasicBlockBuilder
    from cfg_builder import ControlFlowGraph

    # 生成测试IR
    gen = IRGenerator()

    # 示例: 简单程序
    # t1 = a + b
    gen.emit(OpCode.LOAD, result=Address.temp("a"), arg1=Address.variable("a"))
    gen.emit(OpCode.LOAD, result=Address.temp("b"), arg1=Address.variable("b"))
    t1 = gen.new_temp()
    gen.emit_binary(OpCode.ADD, t1, Address.temp("a"), Address.temp("b"))

    # t2 = t1 * c
    t2 = gen.new_temp()
    gen.emit_binary(OpCode.MUL, t2, t1, Address.variable("c"))

    # d = t2
    gen.emit(OpCode.STORE, result=Address.variable("d"), arg1=t2)

    # if t1 > 0 goto L1
    gen.emit_binary(OpCode.GT, Address.temp("t3"), t1, Address.constant(0))
    gen.emit(OpCode.JUMP_IF, result=Address.label("L1"), arg1=Address.temp("t3"))

    # t4 = e + f
    t4 = gen.new_temp()
    gen.emit_binary(OpCode.ADD, t4, Address.variable("e"), Address.variable("f"))

    # L1:
    gen.emit_label("L1")

    instructions = gen.generate()

    # 构建基本块和CFG
    builder = BasicBlockBuilder()
    blocks = builder.build(instructions)
    cfg = ControlFlowGraph(blocks)

    # 活跃性分析
    analysis = LivenessAnalysis(instructions, cfg)
    analysis.analyze()

    # 打印结果
    print("=== 测试IR ===")
    gen.print_ir()
    print()
    print_liveness(analysis)

    # 构建干涉图
    print("\n=== 干涉图 ===")
    ig = build_interference_graph(analysis)
    for var, neighbors in sorted(ig.items()):
        print(f"  {var}: {sorted(neighbors)}")
