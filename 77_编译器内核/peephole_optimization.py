# -*- coding: utf-8 -*-

"""

算法实现：编译器内核 / peephole_optimization



本文件实现 peephole_optimization 相关的算法功能。

"""



from typing import List, Dict, Tuple, Optional, Any, Set

from dataclasses import dataclass



# ========== 指令定义 ==========



@dataclass

class Instruction:

    """指令"""

    opcode: str

    result: Optional[str] = None

    arg1: Optional[str] = None

    arg2: Optional[str] = None

    label: Optional[str] = None

    comment: str = ""

    

    def __repr__(self):

        parts = []

        if self.label:

            parts.append(f"{self.label}:")

        if self.result:

            parts.append(f"{self.result} = ")

            if self.arg1 and self.arg2:

                parts.append(f"{self.arg1} {self.opcode} {self.arg2}")

            elif self.arg1:

                parts.append(f"{self.opcode} {self.arg1}")

            else:

                parts.append(self.opcode)

        elif self.arg1:

            parts.append(f"{self.opcode} {self.arg1}")

        else:

            parts.append(self.opcode)

        return "".join(parts)





# ========== 窥孔优化器 ==========



class PeepholeOptimizer:

    """

    窥孔优化器

    通过局部模式匹配进行指令级优化

    """

    

    def __init__(self):

        self.rules: List[Tuple[str, str]] = []  # (pattern, replacement)

        self.stats = {

            "constant_folding": 0,

            "redundant_load": 0,

            "redundant_store": 0,

            "dead_code": 0,

            "algebraic_simplify": 0,

            "strength_reduce": 0

        }

        self._init_rules()

    

    def _init_rules(self):

        """初始化优化规则"""

        # 常量折叠规则

        self.rules.append(("add r0, r0, 0", "nop"))          # x + 0 = x

        self.rules.append(("sub r0, r0, 0", "nop"))          # x - 0 = x

        self.rules.append(("mul r0, r0, 1", "nop"))          # x * 1 = x

        self.rules.append(("div r0, r0, 1", "nop"))          # x / 1 = x

        self.rules.append(("and r0, r0, -1", "nop"))         # x & -1 = x

        self.rules.append(("or r0, r0, 0", "nop"))           # x | 0 = x

        self.rules.append(("xor r0, r0, 0", "nop"))          # x ^ 0 = x

        

        # 代数简化

        self.rules.append(("mul r0, r0, 0", "mov r0, 0"))     # x * 0 = 0

        self.rules.append(("sub r0, r0, r0", "mov r0, 0"))    # x - x = 0

    

    def optimize(self, instructions: List[Instruction]) -> List[Instruction]:

        """

        执行窥孔优化

        """

        result = []

        i = 0

        

        while i < len(instructions):

            instr = instructions[i]

            

            # 1. 常量折叠

            optimized = self._fold_constants(instr)

            if optimized != instr:

                self.stats["constant_folding"] += 1

                if optimized is None:

                    i += 1

                    continue

                instr = optimized

            

            # 2. 代数简化

            optimized = self._algebraic_simplify(instr)

            if optimized != instr:

                self.stats["algebraic_simplify"] += 1

                if optimized is None:

                    i += 1

                    continue

                instr = optimized

            

            # 3. 窥孔窗口检查（2-3条指令）

            if i + 1 < len(instructions):

                window = [instr, instructions[i + 1]]

                replacement = self._match_peephole(window)

                if replacement:

                    result.append(replacement)

                    i += 2

                    continue

            

            # 4. 冗余加载/存储消除

            if i > 0:

                prev = instructions[i - 1]

                if self._is_redundant_load(instr, prev):

                    self.stats["redundant_load"] += 1

                    i += 1

                    continue

            

            result.append(instr)

            i += 1

        

        return result

    

    def _fold_constants(self, instr: Instruction) -> Optional[Instruction]:

        """常量折叠"""

        if not instr.arg1 or not instr.arg2:

            return instr

        

        # 尝试解析操作数为常量

        try:

            val1 = float(instr.arg1) if instr.arg1.replace('.', '', 1).isdigit() else None

            val2 = float(instr.arg2) if instr.arg2.replace('.', '', 1).isdigit() else None

            

            if val1 is not None and val2 is not None:

                result = self._compute_const_expr(instr.opcode, val1, val2)

                

                if result is not None:

                    # 创建简化指令

                    return Instruction(

                        opcode="mov",

                        result=instr.result,

                        arg1=str(int(result) if result == int(result) else result)

                    )

        except (ValueError, TypeError):

            pass

        

        return instr

    

    def _compute_const_expr(self, op: str, v1: float, v2: float) -> Optional[float]:

        """计算常量表达式"""

        ops = {

            '+': lambda a, b: a + b,

            '-': lambda a, b: a - b,

            '*': lambda a, b: a * b,

            '/': lambda a, b: a / b if b != 0 else None,

            '&': lambda a, b: int(a) & int(b),

            '|': lambda a, b: int(a) | int(b),

            '^': lambda a, b: int(a) ^ int(b),

        }

        

        if op in ops:

            return ops[op](v1, v2)

        return None

    

    def _algebraic_simplify(self, instr: Instruction) -> Optional[Instruction]:

        """代数简化"""

        opcode = instr.opcode

        

        # x + 0 -> x (已通过规则处理)

        # x - x -> 0

        if opcode == "sub" and instr.arg1 == instr.arg2:

            return Instruction("mov", instr.result, arg1="0")

        

        # x * 0 -> 0 (已通过规则处理)

        # x * 1 -> x

        if opcode == "mul" and instr.arg2 == "1":

            return Instruction("mov", instr.result, arg1=instr.arg1)

        

        # x / 1 -> x

        if opcode == "div" and instr.arg2 == "1":

            return Instruction("mov", instr.result, arg1=instr.arg1)

        

        # x & x -> x

        if opcode == "and" and instr.arg1 == instr.arg2:

            return Instruction("mov", instr.result, arg1=instr.arg1)

        

        # x | x -> x

        if opcode == "or" and instr.arg1 == instr.arg2:

            return Instruction("mov", instr.result, arg1=instr.arg1)

        

        return instr

    

    def _match_peephole(self, window: List[Instruction]) -> Optional[Instruction]:

        """匹配窥孔模式"""

        if len(window) < 2:

            return None

        

        # 模式1: load-store冗余

        # load r1, [addr]

        # store [addr], r1

        # -> 可以删除

        if (window[0].opcode == "load" and 

            window[1].opcode == "store" and

            window[0].arg1 == window[1].arg1):

            self.stats["redundant_load"] += 1

            return None

        

        # 模式2: load-after-store same address

        # store [addr], r1

        # load r2, [addr]

        # -> load可以从store的源寄存器直接获取（如果有的话）

        

        # 模式3: 常量操作数交换

        # add r0, r1, 0 -> add r0, 0, r1 (标准化)

        

        return None

    

    def _is_redundant_load(self, instr: Instruction, prev: Instruction) -> bool:

        """检查是否是冗余加载"""

        if instr.opcode == "load" and prev.opcode == "store":

            if instr.arg1 == prev.arg1:

                # 加载紧跟在存储之后，可能是冗余的

                return True

        return False

    

    def get_stats(self) -> Dict[str, int]:

        """获取优化统计"""

        return self.stats.copy()





# ========== 强度削减 ==========



class StrengthReducer:

    """

    强度削减

    将昂贵操作替换为廉价操作

    """

    

    def __init__(self):

        self.rules = self._init_rules()

    

    def _init_rules(self) -> Dict[str, List[Tuple[str, str]]]:

        """初始化强度削减规则"""

        return {

            # 乘法转移位

            "mul_by_pow2": [

                ("mul r0, r1, 2", "add r0, r1, r1"),

                ("mul r0, r1, 4", "add r0, r0, r0; add r0, r0, r0"),

            ],

            # 幂运算

            "pow2_mul": [

                ("mul r0, r1, 2", "shl r0, r1, 1"),

            ],

            # 除以常数转乘法

            "div_by_const": [],

        }

    

    def optimize(self, instructions: List[Instruction]) -> List[Instruction]:

        """执行强度削减"""

        result = []

        

        for instr in instructions:

            # 检查是否符合强度削减模式

            optimized = self._try_strength_reduce(instr)

            

            if optimized:

                result.extend(optimized)

            else:

                result.append(instr)

        

        return result

    

    def _try_strength_reduce(self, instr: Instruction) -> Optional[List[Instruction]]:

        """尝试强度削减"""

        if instr.opcode != "mul" or not instr.arg2:

            return None

        

        try:

            multiplier = int(instr.arg2)

            

            # 2的幂次方乘法 -> 移位

            if multiplier > 0 and (multiplier & (multiplier - 1)) == 0:

                shift_amount = multiplier.bit_length() - 1

                

                return [

                    Instruction("shl", instr.result, arg1=instr.arg1, arg2=str(shift_amount))

                ]

            

            # 乘以0 -> 0

            if multiplier == 0:

                return [Instruction("mov", instr.result, arg1="0")]

            

        except (ValueError, TypeError):

            pass

        

        return None





# ========== 死代码消除 ==========



class DeadCodeEliminator:

    """

    死代码消除器

    移除不会被使用的计算

    """

    

    def __init__(self):

        self.live_vars: Set[str] = set()

    

    def compute_liveness(self, instructions: List[Instruction], 

                         return_vars: List[str] = None) -> Set[str]:

        """

        计算活跃变量

        """

        self.live_vars = set()

        

        if return_vars:

            self.live_vars.update(return_vars)

        

        # 反向扫描

        for instr in reversed(instructions):

            # 定义的变量变为不活跃

            if instr.result and instr.result in self.live_vars:

                self.live_vars.discard(instr.result)

            

            # 使用的变量变为活跃

            if instr.arg1:

                self.live_vars.add(instr.arg1)

            if instr.arg2:

                self.live_vars.add(instr.arg2)

        

        return self.live_vars

    

    def optimize(self, instructions: List[Instruction]) -> List[Instruction]:

        """执行死代码消除"""

        liveness = self.compute_liveness(instructions, return_vars=["retval"])

        

        result = []

        

        for instr in instructions:

            # 检查结果是否被使用

            if instr.result:

                if instr.result in liveness:

                    result.append(instr)

                    # 添加结果到活跃集合（后续指令可能使用）

                    liveness.discard(instr.result)

                    if instr.arg1:

                        liveness.add(instr.arg1)

                    if instr.arg2:

                        liveness.add(instr.arg2)

                else:

                    # 死代码

                    pass

            else:

                result.append(instr)

        

        return result





if __name__ == "__main__":

    print("=" * 60)

    print("窥孔优化演示")

    print("=" * 60)

    

    # 测试代码

    code = [

        Instruction("load", "r1", arg1="[x]"),

        Instruction("add", "r2", arg1="r1", arg2="0"),      # r1 + 0 -> 冗余

        Instruction("sub", "r3", arg1="r2", arg2="r2"),     # r2 - r2 = 0

        Instruction("mul", "r4", arg1="r3", arg2="1"),      # r3 * 1 -> 冗余

        Instruction("store", arg1="[y]", arg2="r4"),

        Instruction("mul", "r5", arg1="r4", arg2="2"),      # 可以优化为移位

        Instruction("add", "r6", arg1="r5", arg2="r5"),

    ]

    

    print("\n原始代码:")

    for instr in code:

        print(f"  {instr}")

    

    # 1. 窥孔优化

    print("\n--- 窥孔优化 ---")

    optimizer = PeepholeOptimizer()

    optimized = optimizer.optimize(code.copy())

    

    print("优化后:")

    for instr in optimized:

        print(f"  {instr}")

    

    print(f"\n优化统计: {optimizer.get_stats()}")

    

    # 2. 强度削减

    print("\n--- 强度削减 ---")

    strength = StrengthReducer()

    reduced = strength.optimize(optimized)

    

    print("强度削减后:")

    for instr in reduced:

        print(f"  {instr}")

    

    # 3. 死代码消除

    print("\n--- 死代码消除 ---")

    dce = DeadCodeEliminator()

    cleaned = dce.optimize(reduced)

    

    print("最终代码:")

    for instr in cleaned:

        print(f"  {instr}")

    

    print("\n窥孔优化策略:")

    print("  1. 常量折叠: 编译时计算常量表达式")

    print("  2. 代数简化: 简化恒等式（如 x+0, x*1）")

    print("  3. 强度削减: 将昂贵操作（如乘法）替换为廉价操作（如移位）")

    print("  4. 冗余消除: 移除重复加载/存储")

    print("  5. 死代码消除: 移除不会被使用的计算")

