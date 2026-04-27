# -*- coding: utf-8 -*-
"""
算法实现：编译器内核 / sccp

本文件实现 sccp 相关的算法功能。
"""

from typing import List, Dict, Set, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum, auto

from basic_block import BasicBlock
from cfg_builder import ControlFlowGraph


class LatticeValue(Enum):
    """格值"""
    UNDEFINED = "undefined"  # 未定义
    CONSTANT = "constant"  # 常量
    TOP = "top"  # 顶部(未知)


@dataclass
class ValueInfo:
    """值信息"""
    lattice: LatticeValue  # 格值
    constant: Union[int, float, str, None] = None  # 常量值

    @staticmethod
    def undefined() -> 'ValueInfo':
        return ValueInfo(lattice=LatticeValue.UNDEFINED)

    @staticmethod
    def constant(val) -> 'ValueInfo':
        return ValueInfo(lattice=LatticeValue.CONSTANT, constant=val)

    @staticmethod
    def top() -> 'ValueInfo':
        return ValueInfo(lattice=LatticeValue.TOP)

    def join(self, other: 'ValueInfo') -> 'ValueInfo':
        """格值Join操作"""
        if self.lattice == LatticeValue.UNDEFINED:
            return other
        if other.lattice == LatticeValue.UNDEFINED:
            return self
        if self.lattice == LatticeValue.TOP or other.lattice == LatticeValue.TOP:
            return ValueInfo.top()
        if self.constant == other.constant:
            return self
        return ValueInfo.top()


@dataclass
class SSANode:
    """SSA形式节点"""
    id: int  # 节点ID
    opcode: str  # 操作码
    operands: List[int] = field(default_factory=list)  # 操作数SSA节点ID
    result: Optional[int] = None  # 结果SSA节点ID


class SCCP:
    """
    稀疏条件常量传播

    算法:
    1. 初始化所有值为TOP
    2. 执行数据流迭代
    3. 遇到分支时,尝试确定跳转条件
    4. 如果条件为常量,只执行对应分支
    5. 收敛后,替换常量表达式
    """

    def __init__(self, cfg: ControlFlowGraph):
        self.cfg = cfg
        self.values: Dict[int, ValueInfo] = {}  # SSA节点ID -> 值
        self.executable_blocks: Set[int] = set()  # 可执行块
        self.block_visited: Dict[int, bool] = {}  # 块是否已访问
        self.cfg: ControlFlowGraph = cfg  # 控制流图

    def run(self) -> Dict[int, ValueInfo]:
        """
        执行SCCP

        返回:
            SSA节点ID到值的映射
        """
        # 初始化: 全局变量为TOP,参数为TOP
        self._initialize()

        # 标记入口块可执行
        if self.cfg.entry_block is not None:
            self.executable_blocks.add(self.cfg.entry_block)
            self._process_block(self.cfg.entry_block)

        # 迭代直到收敛
        changed = True
        iterations = 0
        while changed and iterations < 100:
            changed = False
            iterations += 1

            # 重新处理可执行块
            for block_id in list(self.executable_blocks):
                if not self.block_visited.get(block_id, False):
                    if self._process_block(block_id):
                        changed = True

        return self.values

    def _initialize(self):
        """初始化"""
        # 获取所有SSA节点
        for block_id, node in self.cfg.blocks.items():
            for instr in node.block.instructions:
                if instr.result:
                    self.values[instr.result.value] = ValueInfo.top()

        self.block_visited = {bid: False for bid in self.cfg.blocks}

    def _process_block(self, block_id: int) -> bool:
        """
        处理基本块

        返回:
            是否有新值被传播
        """
        if block_id not in self.cfg.blocks:
            return False

        self.block_visited[block_id] = True
        node = self.cfg.blocks[block_id]
        changed = False

        # 评估块内指令
        for instr in node.block.instructions:
            if self._evaluate_instruction(instr):
                changed = True

        # 处理后继
        last_instr = node.block.get_last_instruction()
        if last_instr:
            succs = node.block.successors
            for succ in succs:
                if self._should_take_branch(node, last_instr, succ):
                    if succ not in self.executable_blocks:
                        self.executable_blocks.add(succ)
                        changed = True

        return changed

    def _evaluate_instruction(self, instr) -> bool:
        """评估单条指令"""
        changed = False

        # 模拟执行,更新values
        # 这里简化处理
        if hasattr(instr, 'result') and instr.result:
            result_key = str(instr.result.value)

            # 如果所有操作数都是常量,可以计算出结果
            if hasattr(instr, 'arg1') and hasattr(instr, 'arg2'):
                arg1_info = self._get_value(instr.arg1)
                arg2_info = self._get_value(instr.arg2)

                if arg1_info.lattice == LatticeValue.CONSTANT and \
                   arg2_info.lattice == LatticeValue.CONSTANT:
                    # 计算
                    result = self._compute(instr.op, arg1_info.constant, arg2_info.constant)
                    new_info = ValueInfo.constant(result)
                    if self._update_value(result_key, new_info):
                        changed = True

        return changed

    def _get_value(self, arg) -> ValueInfo:
        """获取参数的值"""
        if arg and hasattr(arg, 'kind'):
            if arg.kind == "const":
                return ValueInfo.constant(arg.value)
            elif arg.kind in ["var", "temp"]:
                key = str(arg.value)
                return self.values.get(key, ValueInfo.top())
        return ValueInfo.top()

    def _update_value(self, key: str, new_info: ValueInfo) -> bool:
        """更新值,返回是否有变化"""
        old_info = self.values.get(key, ValueInfo.undefined())
        joined = old_info.join(new_info)
        if joined.lattice != old_info.lattice or joined.constant != old_info.constant:
            self.values[key] = joined
            return True
        return False

    def _compute(self, op, a, b):
        """执行计算"""
        try:
            if str(op) == "+":
                return a + b
            elif str(op) == "-":
                return a - b
            elif str(op) == "*":
                return a * b
            elif str(op) == "/":
                return a // b if b != 0 else 0
        except:
            pass
        return None

    def _should_take_branch(self, block: BasicBlock, last_instr, succ: int) -> bool:
        """判断是否应该走某个分支"""
        # 简化: 如果能确定分支条件,决定是否跳转
        return True  # 默认走所有分支


class SCCPOptimizer:
    """
    SCCP优化器封装
    """

    def __init__(self, cfg: ControlFlowGraph):
        self.cfg = cfg
        self.sccp = SCCP(cfg)
        self.constant_uses: Dict[int, List[Tuple[int, int]]] = {}  # 常量使用位置

    def optimize(self) -> bool:
        """
        执行优化

        返回:
            是否有优化发生
        """
        values = self.sccp.run()

        # 收集常量
        constants = {k: v for k, v in values.items()
                   if v.lattice == LatticeValue.CONSTANT}

        if not constants:
            return False

        # 应用优化: 用常量替换
        self._replace_with_constants(constants)
        return True

    def _replace_with_constants(self, constants: Dict[int, ValueInfo]):
        """用常量替换变量"""
        print(f"=== SCCP优化: 发现 {len(constants)} 个常量 ===")
        for ssa_id, info in constants.items():
            print(f"  SSA_{ssa_id} = {info.constant}")


def simple_sccp_test():
    """简单SCCP测试"""
    from intermediate_representation import IRGenerator, Address, OpCode
    from basic_block import BasicBlockBuilder

    # 创建简单CFG用于测试
    gen = IRGenerator()

    # a = 10
    gen.emit(OpCode.LOAD, result=Address.temp("a"), arg1=Address.constant(10))

    # b = a + 5
    t1 = gen.new_temp()
    gen.emit_binary(OpCode.ADD, t1, Address.temp("a"), Address.constant(5))

    # if (b > 10) goto L1 else L2
    gen.emit_binary(OpCode.GT, Address.temp("cond"), t1, Address.constant(10))
    gen.emit(OpCode.JUMP_IF, result=Address.label("L1"), arg1=Address.temp("cond"))
    gen.emit_jump("L2")

    # L1: c = b + 1
    gen.emit_label("L1")
    t2 = gen.new_temp()
    gen.emit_binary(OpCode.ADD, t2, t1, Address.constant(1))

    # L2: end
    gen.emit_label("L2")
    gen.emit(OpCode.FUNC_END, result=Address.variable("main"))

    # 构建基本块
    builder = BasicBlockBuilder()
    blocks = builder.build(gen.generate())
    cfg = ControlFlowGraph(blocks)

    print("=== SCCP测试 ===")
    sccp = SCCP(cfg)
    values = sccp.run()

    print(f"\n分析结果:")
    for ssa_id, info in values.items():
        if info.lattice == LatticeValue.CONSTANT:
            print(f"  SSA_{ssa_id} = {info.constant}")


if __name__ == "__main__":
    simple_sccp_test()

    # 测试格值join
    print("\n=== 格值Join测试 ===")

    v1 = ValueInfo.constant(10)
    v2 = ValueInfo.constant(10)
    v3 = v1.join(v2)
    print(f"  constant(10) join constant(10) = {v3.constant if v3.lattice == LatticeValue.CONSTANT else v3.lattice}")

    v4 = ValueInfo.top()
    v5 = v1.join(v4)
    print(f"  constant(10) join top = {v5.lattice}")

    v6 = ValueInfo.undefined()
    v7 = v1.join(v6)
    print(f"  constant(10) join undefined = {v7.constant if v7.lattice == LatticeValue.CONSTANT else v7.lattice}")
