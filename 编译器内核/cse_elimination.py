# -*- coding: utf-8 -*-
"""
算法实现：编译器内核 / cse_elimination

本文件实现 cse_elimination 相关的算法功能。
"""

from typing import List, Dict, Set, Tuple, Optional, Hashable
from dataclasses import dataclass, field
from collections import defaultdict

from intermediate_representation import TACInstruction, OpCode, Address


@dataclass
class Expression:
    """表达式"""
    op: OpCode  # 操作码
    arg1_val: str  # 第一个操作数的值
    arg2_val: Optional[str] = None  # 第二个操作数的值

    def __hash__(self):
        return hash((self.op, self.arg1_val, self.arg2_val))

    def __eq__(self, other):
        return (self.op == other.op and
                self.arg1_val == other.arg1_val and
                self.arg2_val == other.arg2_val)


@dataclass
class CSEAction:
    """CSE操作"""
    action: str  # "keep", "replace", "remove"
    original_instr: TACInstruction = None
    new_result: Address = None
    instr_index: int = 0


class CSELiminator:
    """
    公共子表达式消除器

    算法:
    1. 扫描指令,维护已见表达式表
    2. 遇到新表达式时,检查是否已有结果
    3. 如果有,复用已有结果;否则记录
    4. 区分Avail表达式和非Avail表达式(由于内存写入可能改变)
    """

    def __init__(self):
        self.avail_expr: Dict[Expression, Tuple[str, Address]] = {}  # 可用表达式
        self.last_def: Dict[str, Address] = {}  # 变量最后定义位置
        self.cse_count = 0  # CSE消除次数
        self.stats = {
            "expressions_seen": 0,
            "cse_applied": 0,
            "code_size_reduction": 0
        }

    def eliminate(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """
        执行CSE

        参数:
            instructions: 原始指令列表

        返回:
            优化后的指令列表
        """
        result: List[TACInstruction] = []
        self.avail_expr.clear()
        self.last_def.clear()

        for i, instr in enumerate(instructions):
            # 检查是否可以用已计算的表达式替代
            if self._can_eliminate(instr):
                expr = self._make_expression(instr)
                if expr in self.avail_expr:
                    # 可以复用
                    result_val, result_addr = self.avail_expr[expr]
                    new_instr = TACInstruction(
                        OpCode.ADD,
                        result=instr.result,
                        arg1=result_addr,
                        arg2=Address.constant(0),
                        comment=f"CSE: reuse {result_val}"
                    )
                    result.append(new_instr)
                    self.cse_count += 1
                    self.stats["cse_applied"] += 1
                    continue

            # 处理指令
            new_instr = self._process_instruction(instr)
            result.append(new_instr)

            # 更新表达式表
            self._update_tables(instr)

        self.stats["expressions_seen"] = len(self.avail_expr)
        self.stats["code_size_reduction"] = self.cse_count

        return result

    def _can_eliminate(self, instr: TACInstruction) -> bool:
        """检查指令是否可以进行CSE"""
        # 只对双目运算进行CSE
        if instr.op not in [OpCode.ADD, OpCode.SUB, OpCode.MUL, OpCode.DIV,
                           OpCode.EQ, OpCode.NE, OpCode.LT, OpCode.GT, OpCode.LE, OpCode.GE]:
            return False

        # 需要两个操作数
        if not instr.arg1 or not instr.arg2:
            return False

        # 操作数必须是变量或常量
        if instr.arg1.kind not in ["var", "temp", "const"] or \
           instr.arg2.kind not in ["var", "temp", "const"]:
            return False

        return True

    def _make_expression(self, instr: TACInstruction) -> Expression:
        """从指令创建表达式"""
        arg1_val = self._get_arg_value(instr.arg1)
        arg2_val = self._get_arg_value(instr.arg2) if instr.arg2 else None
        return Expression(op=instr.op, arg1_val=arg1_val, arg2_val=arg2_val)

    def _get_arg_value(self, arg: Address) -> str:
        """获取操作数的字符串值"""
        if arg.kind == "const":
            return f"#{arg.value}"
        return str(arg.value)

    def _process_instruction(self, instr: TACInstruction) -> TACInstruction:
        """处理指令,更新表"""
        # 记录变量定义
        if instr.result and instr.result.kind in ["var", "temp"]:
            result_name = str(instr.result.value)
            self.last_def[result_name] = instr.result

        return instr

    def _update_tables(self, instr: TACInstruction):
        """更新表达式表和变量表"""
        # 记录表达式结果
        if self._can_eliminate(instr):
            expr = self._make_expression(instr)
            result_name = str(instr.result.value) if instr.result else None
            if result_name and instr.result:
                self.avail_expr[expr] = (result_name, instr.result)

        # 存储指令使某些表达式失效
        if instr.op == OpCode.STORE:
            self._invalidate_store(instr)

    def _invalidate_store(self, instr: TACInstruction):
        """
        存储指令使涉及该内存位置的表达式失效
        简化: 假设store(x, ...)使所有包含x的表达式失效
        """
        if instr.result and instr.result.kind == "var":
            var_name = str(instr.result.value)
            # 移除涉及该变量的表达式
            to_remove = []
            for expr in self.avail_expr:
                if expr.arg1_val == var_name or expr.arg2_val == var_name:
                    to_remove.append(expr)
            for expr in to_remove:
                del self.avail_expr[expr]


class GlobalCSE:
    """
    全局公共子表达式消除
    基于数据流分析
    """

    def __init__(self):
        self.avail_in: Dict[int, Set[Expression]] = {}  # 每点可用表达式
        self.avail_out: Dict[int, Set[Expression]] = {}  # 每点生成的表达式
        self.expr_to_instr: Dict[Expression, int] = {}  # 表达式 -> 首次计算指令
        self.stats = {"global_cse": 0}

    def compute_avail_expr(self, instructions: List[TACInstruction],
                          block_boundaries: List[int]) -> bool:
        """
        计算可用表达式
        使用数据流迭代

        返回:
            是否有新的可用表达式
        """
        n_blocks = len(block_boundaries) + 1
        self.avail_in = {i: set() for i in range(n_blocks)}
        self.avail_out = {i: set() for i in range(n_blocks)}

        # 初始化: entry的avail_in为空
        changed = True
        iterations = 0

        while changed and iterations < 100:
            changed = False
            iterations += 1

            for block_id in range(n_blocks):
                old_out = self.avail_out[block_id].copy()

                # avail_in[block] = intersect of avail_out of predecessors
                # 简化: 取并集
                preds = self._get_predecessors(block_id, block_boundaries)
                if preds:
                    for pred in preds:
                        if pred in self.avail_out:
                            self.avail_in[block_id] |= self.avail_out[pred]

                # 计算gen
                self.avail_out[block_id] = self.avail_in[block_id].copy()
                self._compute_gen(block_id, block_boundaries)

                if self.avail_out[block_id] != old_out:
                    changed = True

        return changed

    def _get_predecessors(self, block_id: int, boundaries: List[int]) -> List[int]:
        """获取前驱块"""
        # 简化: 假设线性结构
        if block_id == 0:
            return []
        return [block_id - 1]

    def _compute_gen(self, block_id: int, boundaries: List[int]):
        """计算块的gen集合"""
        # 获取块内指令
        start = boundaries[block_id - 1] if block_id > 0 else 0
        end = boundaries[block_id] if block_id < len(boundaries) else len(boundaries)

        # 简化: 只处理简单情况


def print_cse_stats(eliminator: CSELiminator):
    """打印CSE统计"""
    print("=== 公共子表达式消除统计 ===")
    stats = eliminator.stats
    print(f"  表达式数: {stats['expressions_seen']}")
    print(f"  CSE应用: {stats['cse_applied']}")
    print(f"  代码减少: {stats['code_size_reduction']} 条指令")


if __name__ == "__main__":
    # 生成测试指令
    # a = b + c
    # d = b + c  <- 可以复用a
    # e = a + d  <- 可以复用
    instructions = [
        TACInstruction(OpCode.ADD, result=Address.temp("t1"),
                      arg1=Address.variable("b"), arg2=Address.variable("c")),
        TACInstruction(OpCode.ADD, result=Address.temp("t2"),
                      arg1=Address.variable("b"), arg2=Address.variable("c")),
        TACInstruction(OpCode.ADD, result=Address.temp("t3"),
                      arg1=Address.temp("t1"), arg2=Address.temp("t2")),
    ]

    print("=== CSE测试 ===")
    print("\n原始指令:")
    for i, instr in enumerate(instructions):
        print(f"  {i}: {instr}")

    # 执行CSE
    eliminator = CSELiminator()
    optimized = eliminator.eliminate(instructions)

    print("\n优化后指令:")
    for i, instr in enumerate(optimized):
        print(f"  {i}: {instr}")

    print_cse_stats(eliminator)

    # 测试有副作用的情况
    print("\n=== 有内存写入的情况 ===")
    instructions2 = [
        TACInstruction(OpCode.ADD, result=Address.temp("t1"),
                      arg1=Address.variable("x"), arg2=Address.variable("y")),
        TACInstruction(OpCode.STORE, result=Address.variable("x"), arg1=Address.constant(100)),
        TACInstruction(OpCode.ADD, result=Address.temp("t2"),
                      arg1=Address.variable("x"), arg2=Address.variable("y")),
    ]

    print("原始指令(带store):")
    for i, instr in enumerate(instructions2):
        print(f"  {i}: {instr}")

    eliminator2 = CSELiminator()
    optimized2 = eliminator2.eliminate(instructions2)

    print("\n优化后:")
    for i, instr in enumerate(optimized2):
        print(f"  {i}: {instr}")

    print_cse_stats(eliminator2)
