# -*- coding: utf-8 -*-
"""
算法实现：编译器内核 / inline_expansion

本文件实现 inline_expansion 相关的算法功能。
"""

from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field

from intermediate_representation import TACInstruction, OpCode, Address


@dataclass
class Function:
    """函数信息"""
    name: str  # 函数名
    params: List[str] = field(default_factory=list)  # 参数列表
    body: List[TACInstruction] = field(default_factory=list)  # 函数体
    return_type: str = "int"  # 返回类型
    local_vars: Set[str] = field(default_factory=set)  # 局部变量
    call_count: int = 0  # 被调用次数


@dataclass
class InlineCandidate:
    """内联候选"""
    call_site: int  # 调用点指令索引
    func_name: str  # 函数名
    func: Function  # 函数信息
    cost: int  # 内联代价
    benefit: int  # 内联收益


class InlineExpander:
    """
    函数内联展开器

    内联策略:
    1. 静态内联: 小函数(小于阈值行数)
    2. 热函数内联: 被频繁调用的函数
    3. 尾调用优化
    """

    def __init__(self, max_inline_size: int = 10, max_depth: int = 3):
        self.max_inline_size = max_inline_size  # 最大内联函数大小
        self.max_depth = max_depth  # 最大内联深度
        self.functions: Dict[str, Function] = {}  # 函数表
        self.inline_history: List[Tuple[str, int]] = []  # 内联历史
        self.stats = {
            "inline_attempts": 0,
            "inline_success": 0,
            "code_growth": 0
        }

    def add_function(self, func: Function):
        """添加函数到函数表"""
        self.functions[func.name] = func

    def find_inline_candidates(self, instructions: List[TACInstruction]) -> List[InlineCandidate]:
        """
        查找可内联的调用点

        参数:
            instructions: 指令列表

        返回:
            内联候选列表
        """
        candidates = []

        for i, instr in enumerate(instructions):
            if instr.op == OpCode.CALL:
                func_name = instr.result.value if instr.result else None
                if func_name and func_name in self.functions:
                    func = self.functions[func_name]
                    cost = len(func.body)
                    benefit = self._calculate_benefit(func)

                    if cost <= self.max_inline_size:
                        candidates.append(InlineCandidate(
                            call_site=i,
                            func_name=func_name,
                            func=func,
                            cost=cost,
                            benefit=benefit
                        ))

        # 按收益排序
        candidates.sort(key=lambda x: x.benefit - x.cost, reverse=True)
        return candidates

    def _calculate_benefit(self, func: Function) -> int:
        """计算内联收益"""
        benefit = 0
        # 调用次数收益
        benefit += func.call_count * 5
        # 小函数收益
        if len(func.body) <= 3:
            benefit += 10
        # 无分支收益
        has_branch = any(instr.op in [OpCode.JUMP, OpCode.JUMP_IF] for instr in func.body)
        if not has_branch:
            benefit += 5
        return benefit

    def inline_call(self, instructions: List[TACInstruction],
                   call_site: int,
                   func: Function,
                   depth: int = 0) -> List[TACInstruction]:
        """
        内联单个调用点

        参数:
            instructions: 原始指令
            call_site: 调用点索引
            func: 函数信息
            depth: 当前内联深度

        返回:
            内联后的指令列表
        """
        if depth >= self.max_depth:
            return instructions

        self.stats["inline_attempts"] += 1

        # 构建参数映射
        call_instr = instructions[call_site]
        param_map = self._build_param_map(call_instr, func)

        # 复制函数体,替换参数
        new_body = self._substitute_body(func.body.copy(), param_map)

        # 替换call指令为函数体
        result = instructions[:call_site] + new_body + instructions[call_site + 1:]

        self.stats["inline_success"] += 1
        self.stats["code_growth"] += len(new_body) - 1

        return result

    def _build_param_map(self, call_instr: TACInstruction, func: Function) -> Dict[str, Address]:
        """构建实参到形参的映射"""
        param_map = {}
        # 简化: 假设参数在call之前的LOAD_PARAM指令中
        # 实际需要分析调用约定
        return param_map

    def _substitute_body(self, body: List[TACInstruction],
                        param_map: Dict[str, Address]) -> List[TACInstruction]:
        """替换函数体中的参数"""
        # 复制并替换
        new_body = []
        for instr in body:
            new_instr = self._substitute_instruction(instr, param_map)
            new_body.append(new_instr)
        return new_body

    def _substitute_instruction(self, instr: TACInstruction,
                               param_map: Dict[str, Address]) -> TACInstruction:
        """替换单条指令中的参数"""
        # 简化: 创建新指令
        new_arg1 = instr.arg1
        new_arg2 = instr.arg2

        return TACInstruction(
            op=instr.op,
            result=instr.result,
            arg1=new_arg1,
            arg2=new_arg2,
            comment=instr.comment
        )

    def expand_all(self, instructions: List[TACInstruction],
                   max_iterations: int = 3) -> List[TACInstruction]:
        """
        尽可能展开所有可内联的调用

        参数:
            instructions: 原始指令
            max_iterations: 最大迭代次数

        返回:
            优化后的指令
        """
        result = instructions

        for iteration in range(max_iterations):
            candidates = self.find_inline_candidates(result)

            if not candidates:
                break

            print(f"\n=== 内联迭代 {iteration + 1} ===")
            print(f"发现 {len(candidates)} 个候选")

            # 选择最佳候选
            best = candidates[0]
            print(f"内联: {best.func_name} (cost={best.cost}, benefit={best.benefit})")

            result = self.inline_call(result, best.call_site, best.func)

        return result

    def should_inline_tail_call(self, func: Function) -> bool:
        """
        判断是否是尾调用,可以优化

        尾调用: 函数最后一步是调用另一个函数
        """
        if not func.body:
            return False

        last_instr = func.body[-1]
        return last_instr.op == OpCode.CALL


def print_inline_stats(expander: InlineExpander):
    """打印内联统计"""
    print("=== 函数内联统计 ===")
    stats = expander.stats
    print(f"  内联尝试: {stats['inline_attempts']}")
    print(f"  内联成功: {stats['inline_success']}")
    print(f"  代码增长: +{stats['code_growth']} 条指令")


def print_functions(funcs: Dict[str, Function]):
    """打印函数表"""
    print("=== 函数表 ===")
    for name, func in funcs.items():
        print(f"\n函数: {name}")
        print(f"  参数: {func.params}")
        print(f"  局部变量: {func.local_vars}")
        print(f"  调用次数: {func.call_count}")
        print(f"  体大小: {len(func.body)}")


if __name__ == "__main__":
    # 创建测试函数
    # int square(int x) { return x * x; }
    square_func = Function(
        name="square",
        params=["x"],
        body=[
            TACInstruction(OpCode.MUL, result=Address.temp("t1"),
                          arg1=Address.variable("x"), arg2=Address.variable("x")),
        ],
        return_type="int"
    )

    # int add(int a, int b) { return a + b; }
    add_func = Function(
        name="add",
        params=["a", "b"],
        body=[
            TACInstruction(OpCode.ADD, result=Address.temp("t1"),
                          arg1=Address.variable("a"), arg2=Address.variable("b")),
        ],
        return_type="int"
    )

    # 测试
    expander = InlineExpander(max_inline_size=10)
    expander.add_function(square_func)
    expander.add_function(add_func)

    print_functions(expander.functions)

    # 生成调用这些函数的指令
    # result = square(5) + add(3, 4)
    instructions = [
        # square(5)
        TACInstruction(OpCode.LOAD_PARAM, arg1=Address.constant(5)),
        TACInstruction(OpCode.CALL, result=Address.temp("sq"), arg1=Address.variable("square")),

        # add(3, 4)
        TACInstruction(OpCode.LOAD_PARAM, arg1=Address.constant(3)),
        TACInstruction(OpCode.LOAD_PARAM, arg1=Address.constant(4)),
        TACInstruction(OpCode.CALL, result=Address.temp("sum"), arg1=Address.variable("add")),

        # add(result, sum)
        TACInstruction(OpCode.LOAD_PARAM, arg1=Address.temp("sq")),
        TACInstruction(OpCode.LOAD_PARAM, arg1=Address.temp("sum")),
        TACInstruction(OpCode.CALL, result=Address.variable("result"), arg1=Address.variable("add")),
    ]

    print("\n=== 原始调用指令 ===")
    for i, instr in enumerate(instructions):
        print(f"  {i}: {instr}")

    # 查找候选
    print("\n=== 内联候选 ===")
    candidates = expander.find_inline_candidates(instructions)
    for cand in candidates:
        print(f"  {cand.func_name}: cost={cand.cost}, benefit={cand.benefit}")

    # 执行内联
    print("\n=== 执行内联 ===")
    result = expander.expand_all(instructions)

    print("\n内联后指令:")
    for i, instr in enumerate(result):
        print(f"  {i}: {instr}")

    print_inline_stats(expander)
