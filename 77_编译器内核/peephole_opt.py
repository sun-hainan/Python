# -*- coding: utf-8 -*-

"""

算法实现：编译器内核 / peephole_opt



本文件实现 peephole_opt 相关的算法功能。

"""



from typing import List, Dict, Tuple, Optional, Callable

from dataclasses import dataclass

from enum import Enum, auto



from intermediate_representation import TACInstruction, OpCode, Address





class OptimizationRule:

    """优化规则"""



    def __init__(self, name: str, match: Callable[[TACInstruction], bool],

                 transform: Callable[[TACInstruction], Optional[List[TACInstruction]]]):

        self.name = name

        self.match = match

        self.transform = transform





@dataclass

class OptimizationResult:

    """优化结果"""

    applied: bool  # 是否应用了优化

    rule_name: str  # 规则名称

    before: str  # 优化前指令

    after: str = ""  # 优化后指令

    new_instructions: List[TACInstruction] = None  # 新指令列表





class PeepholeOptimizer:

    """

    窥孔优化器



    支持的优化:

    1. 常量折叠

    2. 代数简化

    3. 冗余指令消除

    4. 强度削减

    5. 死代码消除

    6. 条件跳转简化

    """



    def __init__(self, window_size: int = 3):

        self.window_size = window_size  # 窥孔窗口大小

        self.rules: List[OptimizationRule] = []

        self.stats = {

            "total_checked": 0,

            "optimizations_applied": 0

        }

        self._register_default_rules()



    def _register_default_rules(self):

        """注册默认优化规则"""



        # 1. 常量折叠: add t1, #1, #2 -> add t1, #1, #3

        self.rules.append(OptimizationRule(

            name="常量折叠",

            match=lambda i: self._is_binop(i) and

                           i.arg1 and i.arg1.kind == "const" and

                           i.arg2 and i.arg2.kind == "const",

            transform=self._fold_constants

        ))



        # 2. 代数简化: add t, x, #0 -> mov t, x

        self.rules.append(OptimizationRule(

            name="代数简化-加0",

            match=lambda i: i.op == OpCode.ADD and

                           i.arg2 and i.arg2.kind == "const" and i.arg2.value == 0,

            transform=lambda i: [TACInstruction(OpCode.ADD, result=i.result,

                                               arg1=i.arg1, arg2=Address.constant(0))]

        ))



        # 3. 代数简化: mul t, x, #1 -> (nop, x is result)

        self.rules.append(OptimizationRule(

            name="代数简化-乘1",

            match=lambda i: i.op == OpCode.MUL and

                           i.arg2 and i.arg2.kind == "const" and i.arg2.value == 1,

            transform=self._identity_mul

        ))



        # 4. 强度削减: mul t, x, #2 -> add t, x, x

        self.rules.append(OptimizationRule(

            name="强度削减-乘2转加法",

            match=lambda i: i.op == OpCode.MUL and

                           i.arg2 and i.arg2.kind == "const" and i.arg2.value == 2,

            transform=lambda i: [TACInstruction(OpCode.ADD, result=i.result,

                                               arg1=i.arg1, arg2=i.arg1)]

        ))



        # 5. 强度削减: mul t, x, #0 -> add t, #0, #0

        self.rules.append(OptimizationRule(

            name="强度削减-乘0",

            match=lambda i: i.op == OpCode.MUL and

                           i.arg2 and i.arg2.kind == "const" and i.arg2.value == 0,

            transform=lambda i: [TACInstruction(OpCode.ADD, result=i.result,

                                               arg1=Address.constant(0),

                                               arg2=Address.constant(0))]

        ))



        # 6. 冗余加载: load t1, x; add t2, t1, #0 -> load x; add t2, x, #0

        self.rules.append(OptimizationRule(

            name="冗余加载消除",

            match=lambda i: False,  # 需要上下文

            transform=lambda i: None

        ))



        # 7. 死代码消除: 无条件跳转到下一条

        self.rules.append(OptimizationRule(

            name="死代码-空跳转",

            match=lambda i: False,  # 需要检查后继

            transform=lambda i: None

        ))



    def optimize(self, instructions: List[TACInstruction]) -> List[TACInstruction]:

        """

        执行窥孔优化



        参数:

            instructions: 输入指令列表



        返回:

            优化后的指令列表

        """

        result = []

        i = 0



        while i < len(instructions):

            instr = instructions[i]

            self.stats["total_checked"] += 1



            # 检查是否有跳转指令形成死代码

            if self._can_eliminate_jump(instr, instructions, i):

                self.stats["optimizations_applied"] += 1

                i += 1  # 跳过跳转

                continue



            # 检查常量折叠和代数简化

            optimized = self._try_optimize(instr)

            if optimized:

                result.extend(optimized)

                self.stats["optimizations_applied"] += 1

            else:

                result.append(instr)



            i += 1



        return result



    def _is_binop(self, instr: TACInstruction) -> bool:

        """检查是否是双目运算"""

        return instr.op in [OpCode.ADD, OpCode.SUB, OpCode.MUL, OpCode.DIV]



    def _fold_constants(self, instr: TACInstruction) -> List[TACInstruction]:

        """常量折叠"""

        if not (instr.arg1 and instr.arg2 and

                instr.arg1.kind == "const" and instr.arg2.kind == "const"):

            return None



        a = instr.arg1.value

        b = instr.arg2.value



        try:

            if instr.op == OpCode.ADD:

                result = a + b

            elif instr.op == OpCode.SUB:

                result = a - b

            elif instr.op == OpCode.MUL:

                result = a * b

            elif instr.op == OpCode.DIV:

                result = a // b if b != 0 else 0

            else:

                return None



            return [TACInstruction(OpCode.ADD, result=instr.result,

                                  arg1=Address.constant(result),

                                  arg2=Address.constant(0),

                                  comment=f"folded: {a}{instr.op.value}{b}={result}")]

        except:

            return None



    def _identity_mul(self, instr: TACInstruction) -> List[TACInstruction]:

        """乘1恒等"""

        if instr.op == OpCode.MUL and instr.arg2 and instr.arg2.kind == "const" and instr.arg2.value == 1:

            # t = x * 1 -> t = x + 0

            return [TACInstruction(OpCode.ADD, result=instr.result,

                                  arg1=instr.arg1,

                                  arg2=Address.constant(0),

                                  comment="identity mul")]

        return None



    def _can_eliminate_jump(self, instr: TACInstruction,

                           instructions: List[TACInstruction],

                           index: int) -> bool:

        """检查是否可以消除跳转"""

        # 无条件跳转到下一条指令

        if instr.op == OpCode.JUMP and instr.result and instr.result.kind == "label":

            target_label = instr.result.value

            if index + 1 < len(instructions):

                next_instr = instructions[index + 1]

                if next_instr.op == OpCode.LABEL and next_instr.result and \

                   next_instr.result.value == target_label:

                    return True

        return False



    def _try_optimize(self, instr: TACInstruction) -> Optional[List[TACInstruction]]:

        """尝试对单条指令应用优化"""

        for rule in self.rules:

            if rule.match(instr):

                result = rule.transform(instr)

                if result:

                    return result

        return None



    def optimize_with_context(self, instructions: List[TACInstruction]) -> List[TACInstruction]:

        """需要上下文信息的优化"""

        result = []

        i = 0



        while i < len(instructions):

            instr = instructions[i]



            # 模式: load t1, x; use t1 -> 直接使用x

            if i + 1 < len(instructions) and instr.op == OpCode.LOAD:

                next_instr = instructions[i + 1]

                if next_instr.op in [OpCode.ADD, OpCode.SUB, OpCode.MUL, OpCode.DIV]:

                    if next_instr.arg1 and str(next_instr.arg1) == str(instr.result):

                        # 可以用变量替换临时变量

                        pass



            result.append(instr)

            i += 1



        return result



    def get_statistics(self) -> Dict[str, int]:

        """获取优化统计"""

        return self.stats.copy()





def print_optimization_stats(optimizer: PeepholeOptimizer):

    """打印优化统计"""

    stats = optimizer.get_statistics()

    print("=== 窥孔优化统计 ===")

    print(f"  检查指令数: {stats['total_checked']}")

    print(f"  优化应用数: {stats['optimizations_applied']}")

    if stats['total_checked'] > 0:

        rate = stats['optimizations_applied'] / stats['total_checked'] * 100

        print(f"  优化率: {rate:.1f}%")





def print_instructions(instructions: List[TACInstruction], title: str = "指令"):

    """打印指令序列"""

    print(f"\n=== {title} ===")

    for i, instr in enumerate(instructions):

        print(f"{i:3d}: {instr}")





if __name__ == "__main__":

    # 生成测试指令

    instructions = [

        # 常量折叠测试

        TACInstruction(OpCode.ADD, result=Address.temp("t1"),

                      arg1=Address.constant(1), arg2=Address.constant(2)),



        # 代数简化-加0

        TACInstruction(OpCode.ADD, result=Address.temp("t2"),

                      arg1=Address.variable("x"), arg2=Address.constant(0)),



        # 强度削减-乘2

        TACInstruction(OpCode.MUL, result=Address.temp("t3"),

                      arg1=Address.variable("y"), arg2=Address.constant(2)),



        # 强度削减-乘0

        TACInstruction(OpCode.MUL, result=Address.temp("t4"),

                      arg1=Address.variable("z"), arg2=Address.constant(0)),



        # 乘1

        TACInstruction(OpCode.MUL, result=Address.temp("t5"),

                      arg1=Address.variable("w"), arg2=Address.constant(1)),



        # 死跳转

        TACInstruction(OpCode.JUMP, result=Address.label("L1")),

        TACInstruction(OpCode.LABEL, result=Address.label("L1")),



        # 存储

        TACInstruction(OpCode.STORE, result=Address.variable("result"),

                      arg1=Address.temp("t4")),

    ]



    print("="*60)

    print("窥孔优化测试")

    print("="*60)



    print_instructions(instructions, "原始指令")



    # 执行优化

    optimizer = PeepholeOptimizer()

    optimized = optimizer.optimize(instructions)



    print_instructions(optimized, "优化后指令")

    print_optimization_stats(optimizer)



    # 测试常量折叠

    print("\n" + "="*60)

    print("常量折叠详细测试")

    print("="*60)



    fold_tests = [

        (OpCode.ADD, 10, 20),

        (OpCode.SUB, 100, 50),

        (OpCode.MUL, 6, 7),

        (OpCode.DIV, 100, 4),

    ]



    for op, a, b in fold_tests:

        instr = TACInstruction(op, result=Address.temp("t"),

                               arg1=Address.constant(a), arg2=Address.constant(b))

        optimizer2 = PeepholeOptimizer()

        result = optimizer2._fold_constants(instr)

        if result:

            print(f"  {a} {op.value} {b} = {result[0].arg1.value}")

        else:

            print(f"  {a} {op.value} {b} = (无法折叠)")

